import re
from pathlib import Path
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path

REQUIRED_FIELDS = ('annual_income', 'tds')
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}

def preprocess_image(path: str):
    suffix = Path(path).suffix.lower()
    if suffix == '.pdf':
        pages = convert_from_path(path, first_page=1, last_page=1, dpi=200)
        if not pages:
            raise ValueError('Could not render PDF document')
        image = cv2.cvtColor(np.array(pages[0]), cv2.COLOR_RGB2BGR)
    else:
        image = cv2.imread(path)
    if image is None: raise ValueError('Could not read document image')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

def extract_fields(path: str) -> dict:
    text = pytesseract.image_to_string(preprocess_image(path))
    patterns = {'annual_income': r'(?:gross salary|annual income|gross total)\D([\d,]+)', 'tds': r'(?:TDS|tax deducted)\D([\d,]+)', 'pan': r'\b([A-Z]{5}\d{4}[A-Z])\b'}
    fields = {}
    missing_fields = []
    validation_errors = []
    for name, pattern in patterns.items():
        match = re.search(pattern, text, re.I)
        value = match.group(1).replace(',', '') if match else None
        if value is None:
            missing_fields.append(name)
        elif name in ('annual_income', 'tds') and float(value) < 0:
            validation_errors.append(f'{name} cannot be negative')
        fields[name] = {'value': value, 'confidence': 'review' if not value else 'detected', 'needs_review': value is None or name in REQUIRED_FIELDS}
    return {'document_type': 'financial_document', 'fields': fields, 'raw_text': text, 'missing_fields': missing_fields, 'validation_errors': validation_errors, 'requires_user_verification': True}
