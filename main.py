from fastapi import FastAPI, UploadFile, File
from PIL import Image
import pytesseract
import io

app = FastAPI(title=  "German Invoice OCR API")

@app.get("/")
def home():
    return {"message": "German Invoice OCR API is running"}

@app.post("/extract-invoice")
async def extract_invoice(file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    
    text = pytesseract.image_to_string(image, lang="deu+eng")
    
    return {
        "filename": file.filename,
        "raw_text": text
    }