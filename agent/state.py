from typing import TypedDict, Optional, List, Dict, Any


class ProcurementState(TypedDict, total=False):
    user_request: str
    request_id: str
    approval_url: str

    request: Dict[str, Any]
    vendors: List[Dict[str, Any]]
    quotes: List[Dict[str, Any]]
    existing_orders: List[Dict[str, Any]]

    duplicate_result: Dict[str, Any]
    budget_result: Dict[str, Any]
    policy_result: Dict[str, Any]
    vendor_result: Dict[str, Any]
    authority_result: Dict[str, Any]

    purchase_order: Optional[Dict[str, Any]]
    verification_result: Optional[Dict[str, Any]]

    next_action: str
    status: str
    explanation: str
    trace: List[str]