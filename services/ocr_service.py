from PIL import Image, ImageFilter, ImageOps
import pytesseract
import io

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