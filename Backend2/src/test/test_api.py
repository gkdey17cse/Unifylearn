import requests

# Test health endpoint
health_response = requests.get("http://127.0.0.1:5000/health")
print("Health:", health_response.json())

# Test query endpoint
user_input = input("Enter user's query : ")
payload = {"query": user_input}
query_response = requests.post("http://127.0.0.1:5000/query", json=payload)
print("Query:", query_response.json())
