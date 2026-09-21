import re
from typing import Optional, Dict, Any

# Recognized educational issuers / platforms for metadata tagging
KNOWN_ISSUERS = [
    ("Coursera", re.compile(r'\bcoursera\b', re.IGNORECASE)),
    ("Udemy", re.compile(r'\budemy\b', re.IGNORECASE)),
    ("edX", re.compile(r'\bedx\b', re.IGNORECASE)),
    ("HackerRank", re.compile(r'\bhackerrank\b', re.IGNORECASE)),
    ("NPTEL", re.compile(r'\bnptel\b', re.IGNORECASE)),
    ("Kaggle", re.compile(r'\bkaggle\b', re.IGNORECASE)),
    ("DataCamp", re.compile(r'\bdatacamp\b', re.IGNORECASE)),
    ("Codecademy", re.compile(r'\bcodecademy\b', re.IGNORECASE)),
    ("LinkedIn Learning", re.compile(r'\blinkedin\s+learning\b', re.IGNORECASE)),
    ("Great Learning", re.compile(r'\bgreat\s+learning\b', re.IGNORECASE)),
    ("National Technical Board", re.compile(r'\bnational\s+technical\s+board\b', re.IGNORECASE)),
]

# Date patterns
DATE_PATTERNS = [
    re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(20\d{2})\b', re.IGNORECASE),
    re.compile(r'\b(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b'),
    re.compile(r'\b(0[1-9]|[12]\d|3[01])/(0[1-9]|1[0-2])/(20\d{2})\b'),
    re.compile(r'\b(20[12]\d)\b'),
]

# Credential ID patterns
CREDENTIAL_ID_PATTERN = re.compile(
    r'(?:certificate\s*(?:id|no\.?|number)|credential\s*(?:id|no\.?|number)|verification\s*(?:code|id|no\.?))[:\s#]+([A-Za-z0-9_-]{5,40})',
    re.IGNORECASE
)

# Recipient lead-in patterns
RECIPIENT_PATTERN = re.compile(
    r'(?:presented to|awarded to|certifies that|certify that|this is to certify that)\s+([A-Za-z\s\.]{2,40})',
    re.IGNORECASE
)


def extract_document_metadata(
    text: str,
    student_full_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract structured metadata from normalized document text:
    - issuer: Detected organization / platform name (for metadata tracking only)
    - issue_date: Detected date or year string
    - credential_id: Detected certificate or credential ID
    - recipient_name: Detected or matched student recipient name
    - text_snippet: First 300 characters of normalized text for auditing
    """
    metadata: Dict[str, Any] = {
        "issuer": None,
        "issue_date": None,
        "credential_id": None,
        "recipient_name": None,
        "recipient_name_matched": False,
        "text_snippet": text[:300].strip() if text else ""
    }

    if not text:
        return metadata

    # 1. Issuer detection (metadata tag only - does NOT confer authenticity)
    for issuer_name, pattern in KNOWN_ISSUERS:
        if pattern.search(text):
            metadata["issuer"] = issuer_name
            break

    # If generic University / Institute pattern matches
    if not metadata["issuer"]:
        generic_match = re.search(r'\b([A-Z][A-Za-z\s]+(?:University|College|Institute|Academy|School of [A-Za-z\s]+))\b', text)
        if generic_match:
            metadata["issuer"] = generic_match.group(1).strip()

    # 2. Date / Year extraction
    for date_pat in DATE_PATTERNS:
        date_match = date_pat.search(text)
        if date_match:
            metadata["issue_date"] = date_match.group(0).strip()
            break

    # 3. Credential ID extraction
    cred_match = CREDENTIAL_ID_PATTERN.search(text)
    if cred_match:
        metadata["credential_id"] = cred_match.group(1).strip()

    # 4. Recipient extraction / verification
    recip_match = RECIPIENT_PATTERN.search(text)
    if recip_match:
        extracted_name = recip_match.group(1).strip().split("\n")[0].strip()
        metadata["recipient_name"] = extracted_name

    # Check match with registered student name
    if student_full_name:
        if student_full_name.lower() in text.lower():
            metadata["recipient_name_matched"] = True
            if not metadata["recipient_name"]:
                metadata["recipient_name"] = student_full_name

    return metadata
