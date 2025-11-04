# ocr_module/views.py
import os
import re
import uuid
import tempfile
import cv2
import numpy as np
import pytesseract
from PIL import Image
from django.conf import settings
from django.utils.text import get_valid_filename
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .serializers import FileUploadSerializer
from pdf2image import convert_from_path

# -------------------------------------------------
# TESSERACT PATH (adjust if you installed elsewhere)
# -------------------------------------------------
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# ----------------------------------------------------------------------
# 1. PRE-PROCESSING – make the image OCR-friendly but keep original shape
# ----------------------------------------------------------------------
def preprocess_and_debug(image_path, unique_name, request):
    img = cv2.imread(image_path)
    if img is None:
        return None, ""

    h, w = img.shape[:2]

    # ---- RESIZE if the image is too small (Tesseract needs ~30 px per char) ----
    if w < 1000:
        scale = 1000 / w
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

    # ---- GRAY → CLAHE → OTSU (best for printed text) ----
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # ---- SAVE DEBUG IMAGE (what Tesseract actually sees) ----
    debug_name = f"DEBUG_{unique_name}"
    debug_path = os.path.join(settings.MEDIA_ROOT, debug_name)
    cv2.imwrite(debug_path, binary)
    debug_url = request.build_absolute_uri(os.path.join(settings.MEDIA_URL, debug_name))

    return Image.fromarray(binary), debug_url


# ----------------------------------------------------------------------
# 2. POST-PROCESSING – ONLY fix known OCR mistakes, keep original case
# ----------------------------------------------------------------------
def fix_ocr_errors(text: str) -> str:
    if not text:
        return ""

    # ---- 1. Known word mis-reads (case-insensitive replace) ----
    word_map = {
        r'\bsrourd\b': 'ROUND',
        r'\brourd\b':  'ROUND',
        r'\bmir\b':    'MIN',
        r'\baverge\b': 'AVERAGE',
        r'\bsum\b':    'SUM',
    }
    for pattern, replacement in word_map.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # ---- 2. Cell-reference fixes (O7 → D7, N6 → D6, I7 → 17) ----
    text = re.sub(r'\bO(\d+)\b', r'D\1', text)   # O7 → D7
    text = re.sub(r'\bN(\d+)\b', r'D\1', text)   # N6 → D6
    text = re.sub(r'\bI(\d+)\b', r'1\1', text)   # I7 → 17

    # ---- 3. Number clean-up (450008 → 450000, '02.05 → 0.05) ----
    text = re.sub(r'(\d)0{2,}', lambda m: m.group(1) + '0' * (len(m.group(0)) - 1), text)
    text = re.sub(r"'0(\d)", r'0.\1', text)      # '02.05 → 0.05
    text = text.replace("'", "")

    # ---- 4. Remove stray symbols that never belong in formulas ----
    text = re.sub(r'[^\w\s\.\+\-\*\/\(\)\[\]\{\}=,;:"\'<>]', ' ', text)

    # ---- 5. Normalise whitespace (keep original line-breaks) ----
    text = re.sub(r'[ \t]+', ' ', text)          # multiple spaces → one
    return text.strip()


# ----------------------------------------------------------------------
# 3. OCR – single best configuration (psm 6 works best for formulas)
# ----------------------------------------------------------------------
def ocr_image(image_path, unique_name, request, lang='eng'):
    pil_img, debug_url = preprocess_and_debug(image_path, unique_name, request)
    if pil_img is None:
        return "Image could not be read", 0, ""

    config = '--oem 3 --psm 6'                     # block of text
    raw = pytesseract.image_to_string(pil_img, lang=lang, config=config)

    # confidence
    data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT, config=config)
    confs = [int(c) for c in data['conf'] if c != '-1' and int(c) > 0]
    conf = round(sum(confs) / len(confs), 2) if confs else 0

    clean = fix_ocr_errors(raw)
    return clean, conf, debug_url


# ----------------------------------------------------------------------
# 4. PDF handling (uses the same pipeline per page)
# ----------------------------------------------------------------------
def ocr_pdf(pdf_path, unique_name, request, lang='eng'):
    with tempfile.TemporaryDirectory() as tmp:
        pages = convert_from_path(pdf_path, dpi=300, fmt='png')
        full_text = ""
        debug_urls = []
        for i, page in enumerate(pages):
            tmp_path = os.path.join(tmp, f"p{i}.png")
            page.save(tmp_path, "PNG")
            txt, _, dbg = ocr_image(tmp_path, f"{unique_name}_p{i}", request, lang)
            full_text += txt + "\n\n"
            if dbg:
                debug_urls.append(dbg)
        return full_text.strip(), 90, debug_urls[0] if debug_urls else ""


# ----------------------------------------------------------------------
# 5. MAIN VIEW
# ----------------------------------------------------------------------
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_file(request):
    serializer = FileUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    file_obj = serializer.validated_data['file']
    safe_name = get_valid_filename(file_obj.name)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    file_path = os.path.join(settings.MEDIA_ROOT, unique_name)

    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    with open(file_path, 'wb+') as f:
        for chunk in file_obj.chunks():
            f.write(chunk)

    file_url = request.build_absolute_uri(os.path.join(settings.MEDIA_URL, unique_name))

    ext = os.path.splitext(file_obj.name)[1].lower()
    lang = request.data.get('lang', 'eng')

    try:
        if ext in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}:
            text, conf, debug_url = ocr_image(file_path, unique_name, request, lang)
        elif ext == '.pdf':
            text, conf, debug_url = ocr_pdf(file_path, unique_name, request, lang)
        else:
            text, conf, debug_url = "Unsupported file type", 0, ""
    except Exception as e:
        text, conf, debug_url = f"Error: {e}", 0, ""

    return Response({
        'message': 'OCR completed – original case preserved',
        'original_name': file_obj.name,
        'url': file_url,
        'extracted_text': text,
        'ocr_confidence': conf,
        'debug_image_url': debug_url,
        'tip': 'Open debug_image_url to see exactly what Tesseract processed'
    }, status=status.HTTP_200_OK)