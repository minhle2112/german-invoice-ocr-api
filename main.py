from fastapi import FastAPI, UploadFile, File
from PIL import Image, ImageFilter, ImageOps
import pytesseract
import io
import re
import requests
import json

app = FastAPI(title=  "German Invoice OCR API")

def extract_with_ai(text):
    prompt = f"""
You are an invoice extraction API.

Return ONLY valid JSON.

Fields:
{{
  "net_total": number,
  "gross_total": number,
  "vat_amount": number,
  "vat_rate": number,
  "currency": null
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
    return json.loads(data["response"])

def fix_vat(data):
    net = data.get("net_total")
    vat = data.get("vat_amount")

    if net and vat:
        data["vat_rate"] = round((vat / net) * 100, 2)

    return data

def preprocess_image(image: Image.Image):
    image = image.convert("L")
    image = ImageOps.autocontrast(image)
    image = image.resize((image.width *2, image.height *2))
    image = image.filter(ImageFilter.SHARPEN)
    return image

def parse_german_amount(value):
    if not value:
        return None

    value = value.replace("€", "").replace("EUR", "").strip()

    # German format: 1.234,56 -> 1234.56
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    else:
        value = value.replace(".", "")

    try:
        return float(value)
    except ValueError:
        return None
    

def calculate_vat(net_total, gross_total):
    if net_total is None or gross_total is None:
        return {
            "vat_rate": None,
            "vat_amount": None
        }

    vat_amount = gross_total - net_total
    vat_rate = (vat_amount / net_total) * 100

    return {
        "vat_rate": round(vat_rate, 2),
        "vat_amount": round(vat_amount, 2)
    }

def extract_first_amount(patterns, text):
    for pattern in patterns:
        result = extract_amount(pattern, text)
        if result is not None:
            return result
    return None

def extract_amount(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    value = match.group(1)
    
    return parse_german_amount(value)


@app.get("/")
def home():
    return {"message": "German Invoice OCR API is running"}

@app.post("/extract-invoice")
async def extract_invoice(file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    processed = preprocess_image(image)
    text = pytesseract.image_to_string(
        processed, 
        lang="deu+eng",
        config="--psm 6")
    
    try:
        ai_data = extract_with_ai(text)
        ai_data = fix_vat(ai_data)
        ai_data["currency"] = "EUR"

        return {
            "filename": file.filename,
            "data": ai_data,
            "raw_text": text
        }

    except Exception as e:
        return {
            "filename": file.filename,
            "error": "AI parsing failed",
            "raw_text": text
        }