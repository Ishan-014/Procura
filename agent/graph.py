from integrations.notion.client import NotionClient
from typing import Dict, Any
import os
import uuid
import requests

from langgraph.graph import StateGraph, END

from agent.state import ProcurementState
from agent.planner import plan_request

from agent.tools import (
    get_vendors,
    get_products,
    get_quotes,
    get_purchase_orders,
    resolve_product,
    get_google_budget,
    get_google_existing_orders,
    record_google_purchase_order,
)

from engines.duplicate.engine import (
    check_duplicate,
    ExistingOrder,
)

from engines.budget.engine import check_budget
from engines.policy.engine import evaluate_policy
from engines.authority.engine import determine_authority

from engines.vendor.engine import (
    select_vendor,
    VendorCandidate,
)

from engines.verification.engine import verify_purchase_order

from integrations.slack.client import SlackClient


VENDOR_API = "http://127.0.0.1:8001"
PROCURA_API = "http://127.0.0.1:8000"


# ---------------------------------------------------------
# 1. UNDERSTAND USER REQUEST
# ---------------------------------------------------------

def understand_request(state: ProcurementState) -> Dict[str, Any]:

    request = plan_request(state["user_request"])

    request_id = state.get(
        "request_id",
        f"REQ-{uuid.uuid4().hex[:6].upper()}",
    )

    return {
        "request": request,
        "request_id": request_id,
        "status": "UNDERSTOOD",
        "trace": state.get("trace", []) + [
            "LLM planner extracted procurement requirements"
        ],
    }


# ---------------------------------------------------------
# 2. VALIDATE REQUEST
# ---------------------------------------------------------

def validate_request(state: ProcurementState):

    request = state["request"]

    required = [
        "product_name",
        "quantity",
        "department",
        "required_by_days",
    ]

    missing = [
        field
        for field in required
        if request.get(field) is None
    ]

    if missing:
        return {
            "status": "BLOCKED",
            "next_action": "REQUEST_MISSING_INFORMATION",
            "explanation": f"Missing required information: {missing}",
            "trace": state.get("trace", []) + [
                f"Validation failed: {missing}"
            ],
        }

    return {
        "status": "VALIDATED",
        "trace": state.get("trace", []) + [
            "Request passed deterministic validation"
        ],
    }


def route_validation(state):

    if state.get("status") == "BLOCKED":
        return END

    return "context"


# ---------------------------------------------------------
# 3. GATHER EXTERNAL CONTEXT
# ---------------------------------------------------------

def gather_context(state):

    vendors = get_vendors()
    products = get_products()
    quotes = get_quotes()

    request = dict(state["request"])

    product = resolve_product(
        request["product_name"],
        products,
    )

    request["product_id"] = product["id"]

    # Google Sheets: company procurement context
    budget = get_google_budget(request["department"])
    existing_orders = get_google_existing_orders()

    return {
        "request": request,
        "vendors": vendors,
        "quotes": quotes,
        "existing_orders": existing_orders,

        "budget_result": {
            "available_budget": budget,
        },

        "status": "CONTEXT_GATHERED",

        "trace": state.get("trace", []) + [
            f"Retrieved {len(vendors)} vendors",
            f"Retrieved {len(products)} products",
            f"Retrieved {len(quotes)} quotes",
            f"Google Sheets: Retrieved {len(existing_orders)} existing orders",
            f"Google Sheets: Retrieved {request['department']} budget → ₹{budget:,.2f}"
            if budget is not None
            else f"Google Sheets: No budget found for {request['department']}",
            f"Resolved product '{request['product_name']}' -> {product['id']}",
        ],
    }


# ---------------------------------------------------------
# 4. DUPLICATE CHECK
# ---------------------------------------------------------

def duplicate_check(state):

    request = dict(state["request"])

    existing_orders = [
        ExistingOrder(
            request_id=str(order.get("Request ID", "")),
            product_id=str(order.get("Product ID", "")),
            quantity=int(order.get("Quantity", 0)),
            status=str(order.get("Status", "")),
        )
        for order in state.get("existing_orders", [])
    ]

    result = check_duplicate(
        product_id=request["product_id"],
        requested_quantity=request["quantity"],
        existing_orders=existing_orders,
    )

    result_dict = {
        "is_duplicate": result.is_duplicate,
        "existing_quantity": result.existing_quantity,
        "additional_quantity": result.additional_quantity,
        "reason": result.reason,
    }

    # Entire request is already covered
    if result.is_duplicate:
        return {
            "duplicate_result": result_dict,
            "status": "BLOCKED",
            "next_action": "STOP_DUPLICATE",
            "explanation": result.reason,
            "trace": state["trace"] + [
                f"Duplicate detected: {result.reason}"
            ],
        }

    # Partial coverage:
    # reduce requested quantity to only what is still needed.
    if result.existing_quantity > 0:
        original_quantity = request["quantity"]
        request["quantity"] = result.additional_quantity

        return {
            "request": request,
            "duplicate_result": result_dict,
            "trace": state["trace"] + [
                f"Duplicate check passed: {result.reason}",
                f"Adjusted purchase quantity: "
                f"{original_quantity} → {result.additional_quantity}",
            ],
        }

    # No existing order
    return {
        "request": request,
        "duplicate_result": result_dict,
        "trace": state["trace"] + [
            f"Duplicate check passed: {result.reason}"
        ],
    }


def route_duplicate(state):

    if state.get("status") == "BLOCKED":
        return END

    return "vendor"


# ---------------------------------------------------------
# 5. VENDOR SELECTION
# ---------------------------------------------------------

def vendor_selection(state):

    request = state["request"]

    product_id = str(request.get("product_id", "")).strip()
    quantity = int(request.get("quantity", 0))

    # --------------------------------------------------------
    # NORMALIZE DEADLINE
    # --------------------------------------------------------
    required_by_days = request.get("required_by_days")

    if required_by_days in (None, "", 0):
        raise ValueError(
            "Missing required delivery deadline for vendor selection."
        )

    required_by_days = int(required_by_days)

    # --------------------------------------------------------
    # BUILD VENDOR CANDIDATES
    # --------------------------------------------------------
    candidates = []

    for quote in state.get("quotes", []):

        # Ignore quotes for other products.
        if str(quote.get("product_id", "")).strip() != product_id:
            continue

        vendor_id = str(quote.get("vendor_id", "")).strip()

        vendor = next(
            (
                v
                for v in state.get("vendors", [])
                if str(v.get("id", "")).strip() == vendor_id
            ),
            None,
        )

        if vendor is None:
            continue

        # Safely normalize quote values.
        unit_price = float(quote.get("unit_price", 0))
        quantity_available = int(
            quote.get("quantity_available", 0)
        )
        delivery_days = int(
            quote.get("delivery_days", 999999)
        )
        warranty_years = int(
            quote.get("warranty_years", 0)
        )
        rating = float(
            vendor.get("rating", 0)
        )

        candidates.append(
            VendorCandidate(
                vendor_id=vendor["id"],
                vendor_name=vendor["name"],
                approved=bool(vendor.get("approved", False)),
                unit_price=unit_price,
                quantity_available=quantity_available,
                delivery_days=delivery_days,
                warranty_years=warranty_years,
                rating=rating,
            )
        )

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------
    if not candidates:
        raise ValueError(
            f"No vendor quotes found for product {product_id}."
        )

    # --------------------------------------------------------
    # DETERMINISTIC VENDOR SELECTION
    # --------------------------------------------------------
    result = select_vendor(
        candidates=candidates,
        quantity=quantity,
        max_delivery_days=required_by_days,
    )

    result_dict = {
        "vendor_id": result.vendor_id,
        "vendor_name": result.vendor_name,
        "total_cost": result.total_cost,
        "reason": result.reason,
    }

    # --------------------------------------------------------
    # TRACE
    # --------------------------------------------------------
    return {
        "vendor_result": result_dict,
        "trace": state["trace"] + [
            f"Evaluated {len(candidates)} vendor candidates",
            f"Applied deadline constraint: {required_by_days} days",
            f"Selected vendor: {result.vendor_name}",
            f"Total cost: ₹{result.total_cost:,.2f}",
        ],
    }


# ---------------------------------------------------------
# 6. BUDGET CHECK
# ---------------------------------------------------------

def budget_check(state):

    vendor = state["vendor_result"]

    # Budget comes from Google Sheets
    available_budget = state.get("budget_result", {}).get(
        "available_budget"
    )

    requested_amount = vendor["total_cost"]

    if available_budget is None:

        result_dict = {
            "within_budget": None,
            "available_budget": None,
            "requested_amount": requested_amount,
            "remaining_budget": None,
            "reason": "No budget found for the department in Google Sheets.",
        }

        return {
            "budget_result": result_dict,
            "trace": state["trace"] + [
                "Budget check: no budget found in Google Sheets"
            ],
        }

    result = check_budget(
        available_budget=available_budget,
        requested_amount=requested_amount,
    )

    result_dict = {
        "within_budget": result.within_budget,
        "available_budget": result.available_budget,
        "requested_amount": result.requested_amount,
        "remaining_budget": result.remaining_budget,
        "reason": result.reason,
    }

    if not result.within_budget:
        return {
            "budget_result": result_dict,
            "status": "BLOCKED",
            "next_action": "BUDGET_EXCEEDED",
            "explanation": result.reason,
            "trace": state["trace"] + [
                f"Budget blocked: {result.reason}"
            ],
        }

    return {
        "budget_result": result_dict,
        "trace": state["trace"] + [
            f"Budget passed: ₹{result.available_budget:,.2f} available → "
            f"₹{result.remaining_budget:,.2f} remaining"
        ],
    }


def route_budget(state):

    if state.get("status") == "BLOCKED":
        return END

    return "policy"


# ---------------------------------------------------------
# 7. POLICY CHECK
# ---------------------------------------------------------

def policy_check(state):

    amount = state["vendor_result"]["total_cost"]

    result = evaluate_policy(amount)

    result_dict = {
        "allowed": result.allowed,
        "reason": result.reason,
        "required_approver": result.required_approver,
    }

    if not result.allowed:
        return {
            "policy_result": result_dict,
            "status": "BLOCKED",
            "next_action": "POLICY_BLOCKED",
            "explanation": result.reason,
            "trace": state["trace"] + [
                f"Policy blocked: {result.reason}"
            ],
        }

    return {
        "policy_result": result_dict,
        "trace": state["trace"] + [
            f"Policy passed: approval required from "
            f"{result.required_approver}"
        ],
    }


def route_policy(state):

    if state.get("status") == "BLOCKED":
        return END

    return "authority"


# ---------------------------------------------------------
# 8. AUTHORITY CHECK
# ---------------------------------------------------------

def authority_check(state):

    request = state["request"]
    policy = state["policy_result"]

    result = determine_authority(
        amount=state["vendor_result"]["total_cost"],
        requester_role=request.get("requester_role") or "UNKNOWN",
        required_approver=policy["required_approver"],
        approval_granted=False,
    )

    authority_result = {
        "can_execute": result.can_execute,
        "requires_human": result.requires_human,
        "approver": result.approver,
        "reason": result.reason,
    }

    return {
        "authority_result": authority_result,
        "status": "REQUIRES_APPROVAL",
        "next_action": "REQUEST_APPROVAL",
        "explanation": result.reason,
        "trace": state["trace"] + [
            f"Human approval required: {result.approver}"
        ],
    }


# ---------------------------------------------------------
# 9. DECISION BRIEF
# ---------------------------------------------------------

def create_decision_brief(state):

    request = state["request"]
    vendor = state["vendor_result"]
    policy = state["policy_result"]

    return {
        "next_action": "WAITING_FOR_APPROVAL",
        "status": "AWAITING_APPROVAL",
        "explanation": (
            f"Purchase of {request['quantity']} units from "
            f"{vendor['vendor_name']} for "
            f"₹{vendor['total_cost']:,.2f} requires "
            f"{policy['required_approver']} approval."
        ),
        "trace": state["trace"] + [
            "Generated executive procurement decision brief",
        ],
    }


# ---------------------------------------------------------
# 10. SEND REAL SLACK APPROVAL
# ---------------------------------------------------------

def request_slack_approval(state):

    request_id = state["request_id"]

    approval_url = (
        f"{PROCURA_API}/agent/approve/{request_id}"
    )

    vendor = state["vendor_result"]
    policy = state["policy_result"]

    slack = SlackClient()

    channel = os.getenv("SLACK_APPROVAL_CHANNEL")

    if not channel:
        raise RuntimeError(
            "SLACK_APPROVAL_CHANNEL is not configured"
        )

    slack.send_approval_request(
        channel=channel,
        request_id=request_id,
        vendor_name=vendor["vendor_name"],
        amount=vendor["total_cost"],
        reason=(
            f"{policy['required_approver']} approval required "
            f"under procurement policy."
        ),
        approval_url=approval_url,
    )

    return {
        "approval_url": approval_url,
        "status": "AWAITING_APPROVAL",
        "next_action": "WAITING_FOR_APPROVAL",
        "explanation": (
            f"Approval request sent to Slack for "
            f"{policy['required_approver']}."
        ),
        "trace": state["trace"] + [
            "Approval request sent to Slack",
            f"Waiting for {policy['required_approver']} approval",
        ],
    }


# ---------------------------------------------------------
# 11. APPROVAL
# ---------------------------------------------------------

def grant_approval(state):

    result = determine_authority(
        amount=state["vendor_result"]["total_cost"],
        requester_role=state["request"].get("requester_role") or "UNKNOWN",
        required_approver=state["policy_result"]["required_approver"],
        approval_granted=True,
    )

    authority_result = {
        "can_execute": result.can_execute,
        "requires_human": result.requires_human,
        "approver": result.approver,
        "reason": result.reason,
    }

    return {
        "authority_result": authority_result,
        "status": "APPROVED",
        "next_action": "EXECUTE",
        "trace": state["trace"] + [
            f"Approval granted by {result.approver}"
        ],
    }


# ---------------------------------------------------------
# 12. EXECUTE PURCHASE
# ---------------------------------------------------------

def execute_purchase(state):

    request = state["request"]
    vendor = state["vendor_result"]

    unit_price = vendor["total_cost"] / request["quantity"]

    payload = {
        "request_id": state["request_id"],
        "vendor_id": vendor["vendor_id"],
        "items": [
            {
                "product_id": request["product_id"],
                "quantity": request["quantity"],
                "unit_price": unit_price,
            }
        ],
        "approved_by": state["authority_result"]["approver"],
    }

    response = requests.post(
        f"{VENDOR_API}/purchase-orders",
        json=payload,
        timeout=10,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Vendor API error {response.status_code}: "
            f"{response.text}"
        )

    purchase_order = response.json()

    # Record completed purchase in Google Sheets
    record_google_purchase_order(purchase_order)

    return {
        "purchase_order": purchase_order,
        "status": "EXECUTED",
        "trace": state["trace"] + [
            f"Created purchase order {purchase_order['id']}",
            f"Google Sheets: Recorded purchase order {purchase_order['id']}",
        ],
    }


# ---------------------------------------------------------
# 13. VERIFY
# ---------------------------------------------------------

def verify_execution(state):

    po = state["purchase_order"]

    actual_response = requests.get(
        f"{VENDOR_API}/purchase-orders/{po['id']}",
        timeout=10,
    )

    if actual_response.status_code >= 400:
        raise RuntimeError(
            f"Verification GET failed "
            f"{actual_response.status_code}: "
            f"{actual_response.text}"
        )

    actual = actual_response.json()

    expected = {
        "request_id": po["request_id"],
        "vendor_id": po["vendor_id"],
        "total_amount": po["total_amount"],
        "approved_by": po["approved_by"],
        "status": po["status"],
    }

    result = verify_purchase_order(
        expected=expected,
        actual=actual,
    )

    verified = getattr(result, "verified", False)

    result_dict = {
        "verified": verified,
        "checks": getattr(result, "checks", {}),
    }

    if verified:
        status = "VERIFIED"
        explanation = (
            "Purchase order independently verified "
            "against vendor state."
        )
    else:
        status = "VERIFICATION_FAILED"
        explanation = (
            "Independent verification detected "
            "a state mismatch."
        )

    return {
        "verification_result": result_dict,
        "status": status,
        "next_action": "COMPLETED" if verified else "RECOVER",
        "explanation": explanation,
        "trace": state["trace"] + [
            f"Independent verification: {verified}"
        ],
    }

def recover_from_vendor_failure(state: ProcurementState, failed_vendor_id: str):
    """
    Replan procurement after the selected vendor becomes unavailable.
    Removes the failed vendor from candidate quotes and selects the
    next qualifying vendor.
    """

    failed_vendor_name = next(
        (
            v["name"]
            for v in state.get("vendors", [])
            if v["id"] == failed_vendor_id
        ),
        failed_vendor_id,
    )

    # Remove failed vendor from available quotes
    remaining_quotes = [
        q
        for q in state.get("quotes", [])
        if q["vendor_id"] != failed_vendor_id
    ]

    recovery_state = dict(state)
    recovery_state["quotes"] = remaining_quotes

    # Re-run deterministic vendor selection
    vendor_result = vendor_selection(recovery_state)

    new_vendor = vendor_result["vendor_result"]

    return {
        "vendor_result": new_vendor,
        "trace": state["trace"] + [
            f"Execution failed: {failed_vendor_name} unavailable",
            "Recovery triggered: replanning vendor selection",
            f"Failed vendor removed from candidate set: {failed_vendor_name}",
            f"Recovery selected alternate vendor: {new_vendor['vendor_name']}",
        ],
    }
# ---------------------------------------------------------
# BUILD GRAPH
# ---------------------------------------------------------

def build_graph():

    graph = StateGraph(ProcurementState)

    graph.add_node("understand", understand_request)
    graph.add_node("validate", validate_request)
    graph.add_node("context", gather_context)
    graph.add_node("duplicate", duplicate_check)
    graph.add_node("vendor", vendor_selection)
    graph.add_node("budget", budget_check)
    graph.add_node("policy", policy_check)
    graph.add_node("authority", authority_check)
    graph.add_node("decision_brief", create_decision_brief)

    graph.add_node("request_approval", request_slack_approval)

    graph.add_node("approval", grant_approval)
    graph.add_node("execute", execute_purchase)
    graph.add_node("verify", verify_execution)

    graph.set_entry_point("understand")

    graph.add_edge("understand", "validate")

    graph.add_conditional_edges(
        "validate",
        route_validation,
        {
            END: END,
            "context": "context",
        },
    )

    graph.add_edge("context", "duplicate")

    graph.add_conditional_edges(
        "duplicate",
        route_duplicate,
        {
            END: END,
            "vendor": "vendor",
        },
    )

    graph.add_edge("vendor", "budget")

    graph.add_conditional_edges(
        "budget",
        route_budget,
        {
            END: END,
            "policy": "policy",
        },
    )

    graph.add_conditional_edges(
        "policy",
        route_policy,
        {
            END: END,
            "authority": "authority",
        },
    )

    graph.add_edge("authority", "decision_brief")
    graph.add_edge("decision_brief", "request_approval")

    # IMPORTANT:
    # request_approval intentionally ends the first run.
    # The API approval endpoint resumes with:
    # approval -> execute -> verify

    graph.add_edge("request_approval", END)

    graph.add_edge("approval", "execute")
    graph.add_edge("execute", "verify")
    graph.add_edge("verify", END)

    return graph.compile()


procurement_graph = build_graph()


# ---------------------------------------------------------
# RESUME AFTER APPROVAL
# ---------------------------------------------------------

def execute_approved_procurement(state: ProcurementState):

    approved_state = dict(state)

    required_keys = [
        "request",
        "vendor_result",
        "policy_result",
        "authority_result",
        "request_id",
        "trace",
    ]

    missing = [
        key for key in required_keys
        if key not in approved_state
    ]

    if missing:
        raise RuntimeError(
            f"Cannot resume procurement. "
            f"Missing state keys: {missing}"
        )

    # --------------------------------------------------------
    # HUMAN APPROVAL
    # --------------------------------------------------------

    approval_result = grant_approval(approved_state)
    approved_state.update(approval_result)

    # --------------------------------------------------------
    # FIRST EXECUTION ATTEMPT
    # --------------------------------------------------------

    try:

        execution_result = execute_purchase(approved_state)
        approved_state.update(execution_result)

    except RuntimeError as e:

        error_message = str(e)

        # Only recover from vendor availability failures.
        if "503" not in error_message:
            raise

        failed_vendor_id = approved_state["vendor_result"]["vendor_id"]

        # ----------------------------------------------------
        # RECOVERY / REPLAN
        # ----------------------------------------------------

        recovery_result = recover_from_vendor_failure(
            approved_state,
            failed_vendor_id,
        )

        approved_state.update(recovery_result)

        # Recalculate policy for the new vendor.
        policy_result = policy_check(approved_state)
        approved_state.update(policy_result)

        if approved_state.get("status") == "BLOCKED":
            return approved_state

        # Re-authorize using the same approval authority.
        authority_result = grant_approval(approved_state)
        approved_state.update(authority_result)

        # ----------------------------------------------------
        # RETRY WITH ALTERNATIVE VENDOR
        # ----------------------------------------------------

        execution_result = execute_purchase(approved_state)
        approved_state.update(execution_result)

    # --------------------------------------------------------
    # INDEPENDENT VERIFICATION
    # --------------------------------------------------------

    verification_result = verify_execution(approved_state)
    approved_state.update(verification_result)

    # --------------------------------------------------------
    # NOTION AUDIT LOG
    # --------------------------------------------------------

    if verification_result.get("verified") is True:

        try:

            from integrations.notion.client import NotionClient

            notion_client = NotionClient()
            notion_client.record_procurement(approved_state)

            approved_state["trace"] = approved_state["trace"] + [
                "Procurement recorded in Notion audit log"
            ]

        except Exception as e:

            approved_state["trace"] = approved_state["trace"] + [
                f"Notion audit logging failed: {str(e)}"
            ]

    return approved_state