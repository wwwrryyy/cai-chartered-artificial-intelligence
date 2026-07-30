"""Document parsing and extraction utilities for CAI."""

from __future__ import annotations

import io
from typing import Any, Dict, List, Tuple

import pdfplumber
from PIL import Image
from PyPDF2 import PdfReader
import pytesseract

from gemma_client import extract_financial_data


def parse_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber with PyPDF2 fallback."""
    if not file_bytes:
        return ""

    text_chunks: List[str] = []

    # Primary extraction with pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_chunks.append(page_text)
    except Exception:  # noqa: BLE001
        text_chunks = text_chunks

    # Fallback extraction with PyPDF2
    if not text_chunks:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_chunks.append(page_text)
        except Exception:  # noqa: BLE001
            text_chunks = text_chunks

    return "\n".join(text_chunks).strip()


def parse_image(file_bytes: bytes) -> str:
    """Extract text from image bytes using OCR."""
    if not file_bytes:
        return ""

    try:
        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception:
        return ""


def extract_financial_fields(text: str, images: List[Any] = None) -> Dict[str, Any]:
    """Use Gemma to extract structured financial fields."""
    return extract_financial_data(text, images)


def validate_extraction(extracted_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate extracted values for basic sanity checks."""
    issues: List[str] = []

    required_numeric_keys = ["annual_income", "basic_salary", "hra_received", "rent_paid"]
    for key in required_numeric_keys:
        value = extracted_data.get(key, 0)
        if not isinstance(value, (int, float)):
            issues.append(f"{key} should be numeric")
        elif value < 0:
            issues.append(f"{key} cannot be negative")

    annual_income = float(extracted_data.get("annual_income", 0) or 0)
    basic_salary = float(extracted_data.get("basic_salary", 0) or 0)

    if annual_income > 0 and basic_salary > annual_income:
        issues.append("Basic salary appears higher than annual income")

    city = str(extracted_data.get("city", "") or "").strip()
    if not city:
        issues.append("City is missing; HRA metro/non-metro logic may be less accurate")

    is_valid = len([i for i in issues if "cannot" in i or "higher" in i]) == 0
    return is_valid, issues