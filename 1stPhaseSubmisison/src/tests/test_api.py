import requests
import json

# Test the API
health_response = requests.get("http://127.0.0.1:5000/health")
print("Health Status:", health_response.status_code)

user_input = input("Enter Natural Language Query: ")
payload = {"query": user_input}
query_response = requests.post("http://127.0.0.1:5000/query", json=payload)

print(f"Query Status Code: {query_response.status_code}")
if query_response.status_code == 200:
    result = query_response.json()
    print("Generated Queries:")
    print(json.dumps(result.get("generated_queries", {}), indent=2))
else:
    print(f"Error: {query_response.text}")
