import os
from PIL import Image
import pytesseract

# Point to Tesseract binary on Windows if not on PATH
_TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(_TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = _TESSERACT_PATH


def extract_text_from_image(file_path: str) -> str:
    """Run OCR on an image file and return extracted text."""
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img)
    return text.strip()
