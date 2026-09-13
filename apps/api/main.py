from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from pathlib import Path
import json

from agent.graph import (
    procurement_graph,
    execute_approved_procurement,
)


app = FastAPI(
    title="Procura API",
    version="0.4.0",
    description="AI Procurement Decision & Execution Agent",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ============================================================
# PERSISTENT APPROVAL STORE
# ============================================================

APPROVAL_STORE = Path("pending_approvals.json")


def load_pending_approvals():
    if not APPROVAL_STORE.exists():
        return {}

    try:
        with open(APPROVAL_STORE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_pending_approvals():
    with open(APPROVAL_STORE, "w", encoding="utf-8") as f:
        json.dump(
            pending_approvals,
            f,
            indent=2,
            ensure_ascii=False,
        )


pending_approvals = load_pending_approvals()


# ============================================================
# REQUEST MODELS
# ============================================================

class ProcurementRequest(BaseModel):
    request_id: str
    requester: str
    requester_role: str
    department: str

    product_id: str
    quantity: int

    required_by_days: int

    available_budget: float

    approval_granted: bool = False
    approved_by: Optional[str] = None


class AgentRequest(BaseModel):
    request: str


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "procura-api",
    }


# ============================================================
# STRUCTURED PROCUREMENT ENDPOINT
# ============================================================

@app.post("/procure")
async def procure(request: ProcurementRequest):

    user_request = (
        f"Procurement request {request.request_id}. "
        f"Requester: {request.requester}. "
        f"Requester role: {request.requester_role}. "
        f"Department: {request.department}. "
        f"Product ID: {request.product_id}. "
        f"Quantity: {request.quantity}. "
        f"Required within {request.required_by_days} days. "
        f"Available budget: ₹{request.available_budget}. "
    )

    result = procurement_graph.invoke({
        "user_request": user_request,
        "request_id": request.request_id,
        "trace": [],
    })

    if result.get("status") == "AWAITING_APPROVAL":

        approval_id = result.get(
            "request_id",
            request.request_id,
        )

        pending_approvals[approval_id] = result
        save_pending_approvals()

    return {
        "status": result.get("status"),
        "request_id": result.get(
            "request_id",
            request.request_id,
        ),
        "request": result.get("request"),
        "vendor": result.get("vendor_result"),
        "budget": result.get("budget_result"),
        "policy": result.get("policy_result"),
        "authority": result.get("authority_result"),
        "purchase_order": result.get("purchase_order"),
        "verification": result.get(
            "verification_result"
        ),
        "explanation": result.get("explanation"),
        "next_action": result.get("next_action"),
        "approval_url": result.get("approval_url"),
        "trace": result.get("trace", []),
    }


# ============================================================
# NATURAL LANGUAGE AGENT ENDPOINT
# ============================================================

@app.post("/agent/procure")
async def agent_procure(request: AgentRequest):

    request_id = f"REQ-{uuid4().hex[:6].upper()}"

    result = procurement_graph.invoke({
        "user_request": request.request,
        "request_id": request_id,
        "trace": [],
    })

    if result.get("status") == "AWAITING_APPROVAL":

        pending_approvals[request_id] = result
        save_pending_approvals()

    return {
        "status": result.get("status"),
        "request_id": request_id,
        "request": result.get("request"),
        "vendor": result.get("vendor_result"),
        "budget": result.get("budget_result"),
        "policy": result.get("policy_result"),
        "authority": result.get("authority_result"),
        "purchase_order": result.get("purchase_order"),
        "verification": result.get(
            "verification_result"
        ),
        "explanation": result.get("explanation"),
        "next_action": result.get("next_action"),
        "approval_url": result.get("approval_url"),
        "trace": result.get("trace", []),
    }


# ============================================================
# APPROVAL PAGE
# ============================================================

@app.get(
    "/agent/approve/{request_id}",
    response_class=HTMLResponse,
)
async def approval_page(request_id: str):

    state = pending_approvals.get(request_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail="Procurement request not found or already processed.",
        )

    vendor = state.get("vendor_result", {})
    authority = state.get("authority_result", {})
    request = state.get("request", {})

    return f"""
    <html>
        <head>
            <title>Procura Approval</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 700px;
                    margin: 60px auto;
                    padding: 30px;
                }}

                .card {{
                    border: 1px solid #ddd;
                    border-radius: 12px;
                    padding: 25px;
                }}

                button {{
                    background: #16a34a;
                    color: white;
                    border: none;
                    padding: 14px 25px;
                    border-radius: 8px;
                    font-size: 16px;
                    cursor: pointer;
                }}
            </style>
        </head>

        <body>

            <div class="card">

                <h1>Procura Procurement Approval</h1>

                <p>
                    <strong>Request:</strong>
                    {request_id}
                </p>

                <p>
                    <strong>Product:</strong>
                    {request.get("product_name", "N/A")}
                </p>

                <p>
                    <strong>Quantity:</strong>
                    {request.get("quantity", "N/A")}
                </p>

                <p>
                    <strong>Vendor:</strong>
                    {vendor.get("vendor_name", "N/A")}
                </p>

                <p>
                    <strong>Total:</strong>
                    ₹{vendor.get("total_cost", 0):,.2f}
                </p>

                <p>
                    <strong>Required Approver:</strong>
                    {authority.get("approver", "N/A")}
                </p>

                <hr>

                <form
                    method="post"
                    action="/agent/approve/{request_id}"
                >
                    <button type="submit">
                        APPROVE PURCHASE
                    </button>
                </form>

            </div>

        </body>
    </html>
    """


# ============================================================
# ACTUAL HUMAN APPROVAL
# ============================================================

@app.post(
    "/agent/approve/{request_id}",
    response_class=HTMLResponse,
)
async def approve_procurement(request_id: str):

    state = pending_approvals.get(request_id)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail="Procurement request not found or already processed.",
        )

    try:

        result = execute_approved_procurement(state)

        # Remove only after successful execution.
        pending_approvals.pop(request_id, None)
        save_pending_approvals()

        purchase_order = result.get("purchase_order", {})
        verification = result.get(
            "verification_result",
            {},
        )

        return f"""
        <html>
            <head>
                <title>Procura - Purchase Completed</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        max-width: 700px;
                        margin: 60px auto;
                        padding: 30px;
                    }}

                    .success {{
                        border: 2px solid #16a34a;
                        border-radius: 12px;
                        padding: 25px;
                    }}
                </style>
            </head>

            <body>

                <div class="success">

                    <h1>✅ Purchase Completed</h1>

                    <p>
                        <strong>Request:</strong>
                        {request_id}
                    </p>

                    <p>
                        <strong>Purchase Order:</strong>
                        {purchase_order.get("id", "N/A")}
                    </p>

                    <p>
                        <strong>Status:</strong>
                        {result.get("status", "N/A")}
                    </p>

                    <p>
                        <strong>Verification:</strong>
                        {verification}
                    </p>

                </div>

            </body>
        </html>
        """

    except Exception as e:

        # IMPORTANT:
        # Keep the approval in the store if execution fails.
        # This allows retrying instead of losing the request.
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ============================================================
# DEBUG / DEMO ENDPOINT
# ============================================================

@app.get("/agent/pending")
def pending_requests():

    return {
        "count": len(pending_approvals),
        "requests": list(pending_approvals.keys()),
    }