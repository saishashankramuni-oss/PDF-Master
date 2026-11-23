"""
PDF Protect/Unlock Service
Handles password-protecting and unlocking PDF files.
"""

import fitz  # PyMuPDF
import io
from typing import Optional, Dict, Any


def protect_pdf(pdf_data: bytes, password: str,
                owner_password: Optional[str] = None,
                user_password: Optional[str] = None,
                permissions: Optional[Dict[str, Any]] = None) -> bytes:
    """
    Password-protect a PDF file.

    Args:
        pdf_data: PDF file bytes
        password: Password to protect the PDF
        owner_password: Owner password (for advanced permissions)
        user_password: User password (for document opening)
        permissions: Dictionary of allowed permissions

    Returns:
        Password-protected PDF as bytes
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    # Set default permissions if not provided
    if permissions is None:
        permissions = {
            "extract": True,
            "content": True,
            "print": True,
            "modify": True,
            "copy": True,
            "modify_annotations": True
        }

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        # Save with encryption
        output_buffer = io.BytesIO()
        # Use password for both user and owner
        enc_password = user_password or password
        doc.save(output_buffer, encryption=fitz.PDF_ENCRYPT_AES_256,
                 user_pw=enc_password, owner_pw=owner_password or enc_password,
                 permissions=0)  # Full permissions by default

        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        try:
            doc.close()
        except:
            pass
        raise RuntimeError(f"PDF protection failed: {str(e)}")


def unlock_pdf(pdf_data: bytes, password: str) -> bytes:
    """
    Unlock a password-protected PDF file.

    Args:
        pdf_data: PDF file bytes (password-protected)
        password: Password to unlock the PDF

    Returns:
        Unlocked PDF as bytes
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        # Check if document is encrypted
        if not doc.is_encrypted:
            # Not encrypted, just return as-is
            output_buffer = io.BytesIO()
            doc.save(output_buffer)
            doc.close()
            output_buffer.seek(0)
            return output_buffer.read()

        # Attempt to decrypt
        if not doc.authenticate(password):
            raise ValueError("Incorrect password provided")

        # Save unlocked version
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        try:
            doc.close()
        except:
            pass
        raise RuntimeError(f"PDF unlock failed: {str(e)}")


def get_protect_info(pdf_data: bytes, password: str,
                     owner_password: Optional[str] = None,
                     user_password: Optional[str] = None,
                     permissions: Optional[Dict[str, Any]] = None) -> dict:
    """
    Get information about PDF protection settings.

    Args:
        pdf_data: PDF file bytes
        password: Password to apply
        owner_password: Owner password
        user_password: User password
        permissions: Dictionary of allowed permissions

    Returns:
        Dictionary with protection information
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        is_encrypted = doc.is_encrypted
        doc.close()

        return {
            "is_encrypted": is_encrypted,
            "can_protect": not is_encrypted,
            "password": "••••••••" if password else None,
            "owner_password": "••••••••" if owner_password else None,
            "user_password": "••••••••" if user_password else None,
            "permissions": permissions or {}
        }
    except Exception as e:
        raise RuntimeError(f"Failed to get protect info: {str(e)}")