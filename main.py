from fastapi import FastAPI, UploadFile, File
from services.ocr_service import extract_text_from_image
from services.invoice_parser import parse_invoice

app = FastAPI(title="German Invoice OCR API")

@app.get("/")
def home():
    return {"message": "German Invoice OCR API is running"}

@app.post("/extract-invoice")
async def extract_invoice(file: UploadFile = File(...)):
    contents = await file.read()

    text = extract_text_from_image(contents)

    try:
        data = parse_invoice(text)

        return {
            "filename": file.filename,
            "data": data,
            "raw_text": text
        }

    except Exception as e:
        print(e)

        return {
            "filename": file.filename,
            "error": "AI parsing failed",
            "raw_text": text
        }