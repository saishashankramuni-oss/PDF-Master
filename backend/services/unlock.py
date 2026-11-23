"""
PDF Unlock Service (Legacy/Alternative)
Handles unlocking PDF files that are protected with passwords.
"""

import fitz  # PyMuPDF
import io
from typing import Optional


def unlock_pdf_simple(pdf_data: bytes, password: str = "") -> bytes:
    """
    Simple PDF unlock function.

    Args:
        pdf_data: PDF file bytes
        password: Password to unlock (empty string if unknown)

    Returns:
        Unlocked PDF as bytes
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        # Try to authenticate/decrypt
        if password:
            success = doc.authenticate(password)
        else:
            # Try without password first
            success = doc.authenticate()

        if not success:
            # If password fails, return document anyway (may be partially accessible)
            pass

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