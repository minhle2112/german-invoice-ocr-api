from fastapi import FastAPI, HTTPException, UploadFile, File
from services.ocr_service import extract_text_from_file
from services.invoice_parser import parse_invoice
from fastapi.responses import Response

from models.en16931 import GermanInvoice
from services.cii_generator import generate_cii_xml
from services.cii_parser import extract_cii_xml_from_file, parse_cii_xml
from services.validator import validate_invoice
from services.xsd_validator import validate_cii_xml

app = FastAPI(title="German Invoice OCR API")

@app.get("/")
def home():
    return {"message": "German Invoice OCR API is running"}

@app.post("/extract-invoice")
async def extract_invoice(file: UploadFile = File(...)):
    contents = await file.read()

    text = extract_text_from_file(contents, file.filename)

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
        

@app.post("/generate/zugferd-cii")
def generate_zugferd_cii(invoice: GermanInvoice):

    xml = generate_cii_xml(invoice)

    return Response(
        content=xml,
        media_type="application/xml"
    )
    
@app.post("/validate/en16931")
def validate_en16931(invoice: GermanInvoice):

    result = validate_invoice(invoice)

    return result

@app.post("/validate/zugferd-xsd")
def validate_zugferd_xsd(invoice: GermanInvoice):
    xml = generate_cii_xml(invoice)
    result = validate_cii_xml(xml)

    return result


@app.post("/convert/zugferd-xml-to-json")
async def convert_zugferd_xml_to_json(file: UploadFile = File(...)):
    contents = await file.read()

    try:
        xml = extract_cii_xml_from_file(contents, file.filename)
        invoice = parse_cii_xml(xml)
        return invoice
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
