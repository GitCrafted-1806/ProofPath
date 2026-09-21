import io
import shutil
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional

from app.core.config import settings
from app.services.text_sanitizer import normalize_document_text


def is_tesseract_available() -> bool:
    """
    Check if the native Tesseract OCR binary is installed and executable on the host system.
    Returns False gracefully if not present.
    """
    if settings.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    try:
        # Check either via shutil.which or test version retrieval
        cmd = pytesseract.pytesseract.tesseract_cmd
        if cmd != "tesseract" and Path(cmd).exists():
            return True
        if shutil.which("tesseract"):
            return True
        # Final test
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def extract_text_from_pdf(file_path: str, max_pages: int = 5) -> Tuple[str, str]:
    """
    Extract text from a PDF document using PyMuPDF.
    If text density is sparse (< 50 chars), attempts OCR fallback via Tesseract if available.
    
    Returns:
        Tuple[str, str]: (extracted_raw_text, extraction_method)
    """
    doc = fitz.open(file_path)
    extracted_pages = []
    num_pages = min(len(doc), max_pages)

    for i in range(num_pages):
        page = doc.load_page(i)
        page_text = page.get_text()
        if page_text:
            extracted_pages.append(page_text)

    combined_text = "\n".join(extracted_pages).strip()

    # If digital PDF contains sufficient embedded text, return directly
    if len(combined_text) >= 50:
        doc.close()
        return combined_text, "PYMUPDF_TEXT"

    # If sparse (< 50 chars), this may be a scanned or image-based PDF
    if is_tesseract_available():
        ocr_pages = []
        try:
            for i in range(num_pages):
                page = doc.load_page(i)
                # Render page at 150 DPI for fast and legible OCR
                pix = page.get_pixmap(dpi=150)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                page_ocr = pytesseract.image_to_string(img)
                if page_ocr:
                    ocr_pages.append(page_ocr)
            doc.close()
            ocr_text = "\n".join(ocr_pages).strip()
            return ocr_text, "PYMUPDF_OCR"
        except Exception:
            doc.close()
            return combined_text, "MANUAL_REVIEW_REQUIRED"
    else:
        # Tesseract not installed on system - graceful fallback
        doc.close()
        return combined_text, "OCR_UNAVAILABLE"


def extract_text_from_image(file_path: str) -> Tuple[str, str]:
    """
    Extract text from an image (JPG/PNG) using Tesseract OCR if available.
    Returns empty string and 'OCR_UNAVAILABLE' if Tesseract is not installed.
    """
    if not is_tesseract_available():
        return "", "OCR_UNAVAILABLE"

    try:
        with Image.open(file_path) as img:
            ocr_text = pytesseract.image_to_string(img)
            return ocr_text.strip(), "TESSERACT_OCR"
    except Exception:
        return "", "MANUAL_REVIEW_REQUIRED"


def parse_document(file_path: str, mime_type: str) -> Tuple[str, str]:
    """
    Unified entry point for document parsing and local text extraction:
    1. Dispatches to PyMuPDF for PDFs, or Tesseract for images.
    2. Applies passive-data text normalization (NFKC, control char removal, 50k char cap).
    
    Returns:
        Tuple[str, str]: (normalized_text, extraction_method)
    """
    if mime_type == "application/pdf":
        raw_text, method = extract_text_from_pdf(file_path)
    elif mime_type in ["image/jpeg", "image/png"]:
        raw_text, method = extract_text_from_image(file_path)
    else:
        raw_text, method = "", "UNSUPPORTED_TYPE"

    normalized_text = normalize_document_text(raw_text)
    return normalized_text, method
