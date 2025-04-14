# frontend/services/api_client.py

import requests
from config import API_URL, PPT_GEN_URL, PDF_GEN_URL, BEARER_TOKEN



def generate_ppt_file(edited_data: dict):
    print(edited_data)
    try:
        headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.post(PPT_GEN_URL, headers=headers, json=edited_data)
        response.raise_for_status()

        data = response.json()
        link = data.get("payload", {}).get("link")
        return {"google_slides_link": link}

    except requests.RequestException as e:
        print(f"PPT GENERATION ERROR: {e}")
        return {"error": str(e)}


def generate_pdf_file(edited_data: dict):
    print(edited_data)
    try:
        headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.post(PDF_GEN_URL, headers=headers, json=edited_data)
        response.raise_for_status()
        data = response.json()
        link = data.get("payload", {}).get("link")
        return {"google_doc_link": link}
    except requests.RequestException as e:
        print(f"PDF GENERATION ERROR: {e}")
        return {"error": str(e)}
    


def search_data(query: str, collections: list[str], top_n_each=5, top_n_total=10, types=None):
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "collections": collections,
        "top_n_each": top_n_each,
        "top_n_total": top_n_total,
        "types": types
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        print(f"API STATUS: {response.status_code}")
        print("API RESPONSE:", response.text)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"API ERROR: {e}")
        return {"error": str(e)}