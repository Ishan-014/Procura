from dotenv import load_dotenv

from integrations.google_sheets.client import GoogleSheetsClient


load_dotenv()


client = GoogleSheetsClient()

print("ENGINEERING BUDGET:")
print(client.get_budget("Engineering"))

print("\nEXISTING ORDERS:")
print(client.get_existing_orders())

print("\nGOOGLE SHEETS OK")