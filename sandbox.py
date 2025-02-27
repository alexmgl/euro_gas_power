import requests

url = f"https://data.nationalgas.com/api/reports"

session = requests.Session()

payload = {"reportName":"Aggregate Physical NTS System Entry Flows (NTSAPF)","gasDay":"2025-02-26"}

response = session.post(f"https://data.nationalgas.com/api/reports", json=payload)

print(response.json())