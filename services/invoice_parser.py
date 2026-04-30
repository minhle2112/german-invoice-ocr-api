from services.ai_service import extract_with_ai
from services.datum_service import normalize_date


def to_float(value):
    if value is None:
        return None

    value = str(value)
    value = value.replace("€", "")
    value = value.replace("EUR", "")
    value = value.replace(" ", "")
    value = value.strip()

    # German number format: 1.350,00 or 1350,00
    if "," in value:
        value = value.replace(".", "").replace(",", ".")

    try:
        return float(value)
    except:
        return None

def fix_vat(data):
    
    net = data.get("net_total")
    gross = data.get("gross_total")

    if net is None or gross is None or net <= 0:
        return data

    vat_amount = round(gross - net, 2)
    vat_rate = round((vat_amount / net) * 100, 2)

    data["vat_amount"] = vat_amount
    data["vat_rate"] = vat_rate

    return data

def clean_iban(value):
    if not value:
        return None

    return str(value).replace(" ", "").strip()

def clean_vat_id(value):
    if not value:
        return None

    return str(value).replace(" ", "").strip()

def parse_invoice(text):
    ai_data = extract_with_ai(text)

    ai_data["net_total"] = to_float(ai_data.get("net_total"))
    ai_data["gross_total"] = to_float(ai_data.get("gross_total"))
    ai_data["vat_amount"] = to_float(ai_data.get("vat_amount"))
    
    
    
    ai_data = fix_vat(ai_data)
    
    ai_data["invoice_date"] = normalize_date(ai_data.get("invoice_date"))
    
    ai_data["iban"] = clean_iban(ai_data.get("iban"))
    ai_data["vendor_vat_id"] = clean_vat_id(ai_data.get("vendor_vat_id"))

    
    ai_data["currency"] = "EUR"

    return ai_data