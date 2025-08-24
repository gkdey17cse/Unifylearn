import requests

# Test health endpoint
health_response = requests.get("http://127.0.0.1:5000/health")
print("Health Status:", health_response.status_code)
print("Health Response:", health_response.text)

# Test query endpoint
user_input = "show me only courses from SIMplilern and Udacity on Deep Learning"
payload = {"query": user_input}
query_response = requests.post("http://127.0.0.1:5000/query", json=payload)

print(f"\nQuery Status Code: {query_response.status_code}")
print(f"Query Response (first 500 chars):\n{query_response.text[:500]}")