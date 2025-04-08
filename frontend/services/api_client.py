# frontend/services/api_client.py

import requests
from frontend.config import API_URL, BEARER_TOKEN

def search_data(query: str, collections: list[str], top_n_each=5, top_n_total=10):
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "collections": collections,
        "top_n_each": top_n_each,
        "top_n_total": top_n_total
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        print(f"API STATUS: {response.status_code}")
        print("API RESPONSE:", response.text)  # full response
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"API ERROR: {e}")
        return {"error": str(e)}