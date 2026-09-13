from integrations.google_sheets.client import GoogleSheetsClient

import requests

VENDOR_API = "http://127.0.0.1:8001"


def get_vendors():
    response = requests.get(f"{VENDOR_API}/vendors")
    response.raise_for_status()
    return response.json()


def get_products():
    response = requests.get(f"{VENDOR_API}/products")
    response.raise_for_status()
    return response.json()


def get_quotes():
    response = requests.get(f"{VENDOR_API}/quotes")
    response.raise_for_status()
    return response.json()


def get_purchase_orders():
    response = requests.get(f"{VENDOR_API}/purchase-orders")
    response.raise_for_status()
    return response.json()


def resolve_product(product_name: str, products: list) -> dict:
    name = product_name.lower()

    for product in products:
        if name in product["name"].lower():
            return product

    raise ValueError(
        f"No product found matching: {product_name}"
    )

def get_google_budget(department: str):
    client = GoogleSheetsClient()
    return client.get_budget(department)


def get_google_existing_orders():
    client = GoogleSheetsClient()
    return client.get_existing_orders()


def record_google_purchase_order(purchase_order: dict):
    client = GoogleSheetsClient()
    return client.record_purchase_order(purchase_order)