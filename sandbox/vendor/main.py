from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
import uuid

app = FastAPI(
    title="Procura Vendor Sandbox",
    version="1.1.0",
    description="Deterministic vendor/procurement environment for Procura."
)


# ============================================================
# DATA MODELS
# ============================================================

class Vendor(BaseModel):
    id: str
    name: str
    approved: bool
    rating: float
    categories: List[str]


class Product(BaseModel):
    id: str
    name: str
    category: str
    specifications: dict


class Quote(BaseModel):
    id: str
    vendor_id: str
    product_id: str
    unit_price: float
    quantity_available: int
    delivery_days: int
    warranty_years: int
    valid_until: str
    timestamp: str


class PurchaseOrderItem(BaseModel):
    product_id: str
    quantity: int
    unit_price: float


class PurchaseOrderCreate(BaseModel):
    request_id: str
    vendor_id: str
    items: List[PurchaseOrderItem]
    approved_by: str


class PurchaseOrder(BaseModel):
    id: str
    request_id: str
    vendor_id: str
    items: List[PurchaseOrderItem]
    total_amount: float
    approved_by: str
    status: str
    created_at: str


# ============================================================
# DETERMINISTIC SANDBOX STATE
# ============================================================

vendors = [
    Vendor(
        id="V001",
        name="Vendor A",
        approved=True,
        rating=4.7,
        categories=["laptop", "hardware"]
    ),
    Vendor(
        id="V002",
        name="Vendor B",
        approved=True,
        rating=4.4,
        categories=["laptop", "hardware"]
    ),
    Vendor(
        id="V003",
        name="Vendor C",
        approved=True,
        rating=4.6,
        categories=["laptop", "hardware"]
    ),
    Vendor(
        id="V004",
        name="Vendor D",
        approved=False,
        rating=4.8,
        categories=["laptop", "hardware"]
    ),
]


products = [
    Product(
        id="P001",
        name="Engineering Laptop Pro",
        category="laptop",
        specifications={
            "cpu": "Intel Core i7",
            "ram_gb": 32,
            "storage_gb": 1000
        }
    )
]


quotes = [
    Quote(
        id="Q001",
        vendor_id="V001",
        product_id="P001",
        unit_price=72000,
        quantity_available=30,
        delivery_days=3,
        warranty_years=3,
        valid_until="2026-10-01",
        timestamp=datetime.utcnow().isoformat()
    ),
    Quote(
        id="Q002",
        vendor_id="V002",
        product_id="P001",
        unit_price=65000,
        quantity_available=50,
        delivery_days=18,
        warranty_years=2,
        valid_until="2026-10-01",
        timestamp=datetime.utcnow().isoformat()
    ),
    Quote(
        id="Q003",
        vendor_id="V003",
        product_id="P001",
        unit_price=69500,
        quantity_available=30,
        delivery_days=7,
        warranty_years=3,
        valid_until="2026-10-01",
        timestamp=datetime.utcnow().isoformat()
    ),
]


purchase_orders: List[PurchaseOrder] = []

# Vendors placed in this set deliberately fail execution.
# Used only for deterministic reliability/recovery tests.
vendor_failures = set()


# ============================================================
# VENDORS
# ============================================================

@app.get("/vendors", response_model=List[Vendor])
def get_vendors():
    return vendors


@app.get("/vendors/{vendor_id}", response_model=Vendor)
def get_vendor(vendor_id: str):
    for vendor in vendors:
        if vendor.id == vendor_id:
            return vendor

    raise HTTPException(
        status_code=404,
        detail="Vendor not found"
    )


# ============================================================
# PRODUCTS
# ============================================================

@app.get("/products", response_model=List[Product])
def get_products():
    return products


@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: str):
    for product in products:
        if product.id == product_id:
            return product

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )


# ============================================================
# QUOTES
# ============================================================

@app.get("/quotes", response_model=List[Quote])
def get_quotes():
    return quotes


@app.get("/quotes/{quote_id}", response_model=Quote)
def get_quote(quote_id: str):
    for quote in quotes:
        if quote.id == quote_id:
            return quote

    raise HTTPException(
        status_code=404,
        detail="Quote not found"
    )


# ============================================================
# TEST FAILURE CONTROLS
# ============================================================

@app.post("/test/vendor-failure/{vendor_id}")
def set_vendor_failure(vendor_id: str):

    vendor = next(
        (v for v in vendors if v.id == vendor_id),
        None
    )

    if vendor is None:
        raise HTTPException(
            status_code=404,
            detail="Vendor not found"
        )

    vendor_failures.add(vendor_id)

    return {
        "vendor_id": vendor_id,
        "failed": True,
        "message": f"Vendor {vendor_id} will fail during execution."
    }


@app.post("/test/vendor-recover/{vendor_id}")
def recover_vendor(vendor_id: str):

    vendor_failures.discard(vendor_id)

    return {
        "vendor_id": vendor_id,
        "failed": False,
        "message": f"Vendor {vendor_id} is available again."
    }


@app.get("/test/vendor-failures")
def get_vendor_failures():
    return {
        "failed_vendors": list(vendor_failures)
    }


# ============================================================
# PURCHASE ORDERS
# ============================================================

@app.get("/purchase-orders", response_model=List[PurchaseOrder])
def get_purchase_orders():
    return purchase_orders


@app.get("/purchase-orders/{po_id}", response_model=PurchaseOrder)
def get_purchase_order(po_id: str):

    for po in purchase_orders:
        if po.id == po_id:
            return po

    raise HTTPException(
        status_code=404,
        detail="Purchase order not found"
    )


@app.post("/purchase-orders", response_model=PurchaseOrder)
def create_purchase_order(data: PurchaseOrderCreate):

    # --------------------------------------------------------
    # Validate vendor
    # --------------------------------------------------------

    vendor = next(
        (v for v in vendors if v.id == data.vendor_id),
        None
    )

    if vendor is None:
        raise HTTPException(
            status_code=400,
            detail="Vendor does not exist"
        )

    # --------------------------------------------------------
    # Deterministic vendor failure
    # --------------------------------------------------------

    if data.vendor_id in vendor_failures:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Vendor {data.vendor_id} is temporarily unavailable"
            )
        )

    if not vendor.approved:
        raise HTTPException(
            status_code=403,
            detail="Vendor is not approved"
        )

    # --------------------------------------------------------
    # Validate products and inventory
    # --------------------------------------------------------

    total_amount = 0

    for item in data.items:

        product = next(
            (
                p for p in products
                if p.id == item.product_id
            ),
            None
        )

        if product is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Product {item.product_id} "
                    f"does not exist"
                )
            )

        quote = next(
            (
                q for q in quotes
                if (
                    q.vendor_id == data.vendor_id
                    and q.product_id == item.product_id
                )
            ),
            None
        )

        if quote is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No quote exists for this "
                    "vendor/product"
                )
            )

        if item.quantity > quote.quantity_available:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Insufficient inventory. "
                    f"Available={quote.quantity_available}, "
                    f"Requested={item.quantity}"
                )
            )

        total_amount += (
            item.quantity * item.unit_price
        )

    # --------------------------------------------------------
    # Create PO
    # --------------------------------------------------------

    po = PurchaseOrder(
        id=f"PO-{uuid.uuid4().hex[:8].upper()}",
        request_id=data.request_id,
        vendor_id=data.vendor_id,
        items=data.items,
        total_amount=total_amount,
        approved_by=data.approved_by,
        status="CREATED",
        created_at=datetime.utcnow().isoformat()
    )

    purchase_orders.append(po)

    # --------------------------------------------------------
    # Update inventory
    # --------------------------------------------------------

    for item in data.items:

        for quote in quotes:

            if (
                quote.vendor_id == data.vendor_id
                and quote.product_id == item.product_id
            ):
                quote.quantity_available -= item.quantity

    return po


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "procura-vendor-sandbox"
    }