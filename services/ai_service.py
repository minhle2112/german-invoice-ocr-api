import requests
import json

def extract_with_ai(text):
    prompt = f"""
You are an invoice extraction API.

Return ONLY valid JSON.

Fields:
{{
    "vendor_name": null,
    "vendor_vat_id": null,
    
    "invoice_number": null,
    "invoice_date": null,
    
    "net_total": null,
    "gross_total": null,
    "vat_amount": null,
    "vat_rate": null,
    "currency": null
    
    "iban" : null,
}}

Text:
{text}
"""

    res = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen3:8b",
            "prompt": prompt,
            "format": "json",
            "stream": False
        }
    )

    data = res.json()
    print(json.loads(data["response"]))
    return json.loads(data["response"])