from integrations.notion.client import NotionClient

client = NotionClient()

client.record_procurement({
    "request_id": "NOTION-TEST-001",
    "vendor_result": {
        "vendor_name": "Vendor C",
        "total_cost": 2085000,
        "reason": "Meets deadline and company policy."
    },
    "status": "VERIFIED",
    "verification_result": {
        "verified": True
    }
})

print("NOTION OK")