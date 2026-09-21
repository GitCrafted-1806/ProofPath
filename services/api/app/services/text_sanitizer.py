import re
import unicodedata
from typing import Optional

# Maximum characters allowed for downstream extraction/preview to prevent ReDoS / memory exhaustion
MAX_DOCUMENT_TEXT_LENGTH = 50000


def normalize_document_text(text: Optional[str]) -> str:
    """
    Safely normalize extracted document text as passive data:
    1. Unicode NFKC normalization
    2. Control character removal (preserving standard whitespace: newline, carriage return, tab)
    3. Whitespace normalization (collapsing redundant blank lines and trailing spaces)
    4. Truncation to 50,000 characters maximum

    Note: Phase 2 deliberately treats extracted text strictly as passive data without
    altering legitimate document phrases.
    """
    if not text:
        return ""

    # 1. Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", text)

    # 2. Control character removal (strip 0x00-0x1F and 0x7F-0x9F except \t (0x09), \n (0x0A), \r (0x0D))
    cleaned_chars = []
    for char in normalized:
        cp = ord(char)
        if cp in (9, 10, 13) or (cp >= 32 and cp != 127 and not (128 <= cp <= 159)):
            cleaned_chars.append(char)
        else:
            cleaned_chars.append(" ")
    cleaned_text = "".join(cleaned_chars)

    # 3. Whitespace normalization:
    # Collapse multiple consecutive spaces (excluding newlines)
    cleaned_text = re.sub(r'[^\S\r\n]+', ' ', cleaned_text)
    # Collapse more than 2 consecutive newlines into 2
    cleaned_text = re.sub(r'(\r?\n\s*){3,}', '\n\n', cleaned_text)
    # Strip leading and trailing whitespace
    cleaned_text = cleaned_text.strip()

    # 4. Truncation guard to maximum 50,000 characters
    if len(cleaned_text) > MAX_DOCUMENT_TEXT_LENGTH:
        cleaned_text = cleaned_text[:MAX_DOCUMENT_TEXT_LENGTH]

    return cleaned_text
