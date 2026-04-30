from PIL import Image, ImageFilter, ImageOps
import pytesseract
import io
import fitz # pymupdf

def preprocess_image(image: Image.Image):
    image = image.convert("RGBA")
    image = image.convert("L")
    image = ImageOps.autocontrast(image)
    image = image.resize((image.width * 2, image.height * 2))
    image = image.filter(ImageFilter.SHARPEN)
    return image

def extract_text_from_image(contents: bytes):
    image = Image.open(io.BytesIO(contents))
    processed = preprocess_image(image)

    text = pytesseract.image_to_string(
        processed,
        lang="deu+eng",
        config="--psm 6"
    )

    return text

def extract_text_from_pdf(contents: bytes):
    doc = fitz.open(stream=contents, filetype="pdf")

    text = ""

    # 1. Try direct text extraction
    for page in doc:
        text += page.get_text() + "\n"

    if text.strip():
        return text

    # 2. Fallback: OCR PDF pages
    ocr_text = ""

    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        processed = preprocess_image(img)

        ocr_text += pytesseract.image_to_string(
            processed,
            lang="deu+eng",
            config="--psm 6"
        ) + "\n"

    return ocr_text

def extract_text_from_file(contents: bytes, filename: str):
    if filename.lower().endswith(".pdf"):
        return extract_text_from_pdf(contents)

    return extract_text_from_image(contents)