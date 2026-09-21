import io
import os
import re
import uuid
import hashlib
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image

from app.core.config import settings

# Magic byte signatures
MAGIC_BYTES = {
    ".pdf": b"%PDF-",
    ".png": b"\x89PNG\r\n\x1a\n",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
}

# MIME type mapping
MIME_TO_EXT = {
    "application/pdf": [".pdf"],
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
}


def sanitize_filename(filename: Optional[str]) -> str:
    """Sanitize the original filename to prevent directory traversal and null byte injections."""
    if not filename:
        return "unnamed_document"
    # Take only the base name (no path components)
    clean_name = Path(filename).name
    # Remove null bytes and non-printable characters
    clean_name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', clean_name)
    # Strip dangerous characters
    clean_name = re.sub(r'[^\w\s\.-]', '_', clean_name).strip()
    return clean_name or "unnamed_document"


def validate_file_header(filename: str, content_type: Optional[str], initial_bytes: bytes) -> str:
    """
    Validate file extension, declared MIME type, and binary magic bytes.
    Returns the normalized safe file extension.
    Raises HTTPException(400) if validation fails.
    """
    clean_name = sanitize_filename(filename)
    ext = Path(clean_name).suffix.lower()

    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Validate declared MIME type if provided
    if content_type:
        normalized_ct = content_type.lower().split(";")[0].strip()
        if normalized_ct not in settings.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MIME type '{normalized_ct}' is not permitted. Allowed: {', '.join(settings.ALLOWED_MIME_TYPES)}"
            )

    # Validate magic bytes
    expected_magic = MAGIC_BYTES.get(ext)
    if expected_magic and not initial_bytes.startswith(expected_magic):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File signature does not match expected format for '{ext}'. File may be corrupted or spoofed."
        )

    # For images, verify image integrity using PIL
    if ext in [".png", ".jpg", ".jpeg"]:
        try:
            with Image.open(io.BytesIO(initial_bytes)) as img:
                img.verify()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file is corrupted or could not be decoded."
            )

    return ext


async def save_upload_file(
    upload_file: UploadFile,
    student_id: str
) -> Tuple[str, str, int, str, str]:
    """
    Stream and securely save an uploaded file with size and content validation.
    
    Returns:
        Tuple of:
        - file_path: Absolute storage path on disk
        - sanitized_original_filename: Cleaned display name
        - file_size: Total file size in bytes
        - sha256: SHA-256 hexadecimal hash
        - mime_type: Verified MIME type string
    
    Raises:
        HTTPException(400): If file header or format is invalid.
        HTTPException(413): If file size exceeds MAX_UPLOAD_SIZE_BYTES (5 MB).
    """
    original_filename = sanitize_filename(upload_file.filename)

    # Read first 8KB chunk to inspect file signature before full streaming
    first_chunk = await upload_file.read(8192)
    if not first_chunk:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    # Validate header & magic bytes
    safe_ext = validate_file_header(original_filename, upload_file.content_type, first_chunk)

    # Determine standardized MIME type
    if safe_ext == ".pdf":
        mime_type = "application/pdf"
    elif safe_ext in [".jpg", ".jpeg"]:
        mime_type = "image/jpeg"
    elif safe_ext == ".png":
        mime_type = "image/png"
    else:
        mime_type = "application/octet-stream"

    # Prepare secure destination directory: data/uploads/{student_id}/
    student_storage_dir = Path(settings.UPLOAD_DIR) / student_id
    student_storage_dir.mkdir(parents=True, exist_ok=True)

    # Generate non-guessable random storage filename
    random_filename = f"{uuid.uuid4().hex}{safe_ext}"
    dest_path = student_storage_dir / random_filename

    hasher = hashlib.sha256()
    hasher.update(first_chunk)
    total_size = len(first_chunk)

    if total_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
            detail=f"File exceeds maximum allowed upload size of 5 MB."
        )

    # Stream the file to disk in 64KB chunks
    chunk_size = 65536
    try:
        with open(dest_path, "wb") as f:
            f.write(first_chunk)
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > settings.MAX_UPLOAD_SIZE_BYTES:
                    # Clean up partial file immediately
                    f.close()
                    if dest_path.exists():
                        dest_path.unlink()
                    raise HTTPException(
                        status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                        detail=f"File exceeds maximum allowed upload size of 5 MB."
                    )
                hasher.update(chunk)
                f.write(chunk)
    except HTTPException:
        # Re-raise size or format HTTP exceptions
        raise
    except Exception as e:
        # Clean up partial file on unexpected write failure
        if dest_path.exists():
            dest_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    # For images, perform a final full-image format verification on the written file
    if safe_ext in [".png", ".jpg", ".jpeg"]:
        try:
            with Image.open(dest_path) as img:
                img.verify()
        except Exception:
            if dest_path.exists():
                dest_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file is corrupted or could not be decoded."
            )

    return (
        str(dest_path.resolve()),
        original_filename,
        total_size,
        hasher.hexdigest(),
        mime_type
    )


def delete_file(file_path: Optional[str]) -> bool:
    """Safely delete a stored file from disk if it exists."""
    if not file_path:
        return False
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
            return True
    except OSError:
        pass
    return False
