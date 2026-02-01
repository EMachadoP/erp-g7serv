import requests
import json

url = "http://localhost:8001/ai/processar/"
payload = {
    "mensagem": "ERP G7Serv 100% funcional!",
    "nome": "Deploy Final"
}
headers = {
    "Content-Type": "application/json"
}

print(f"Testing URL: {url}")
try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
