"""
PDF Repair Service
Handles repairing corrupted or damaged PDF files.
"""

import fitz  # PyMuPDF
import io
from typing import Optional, Dict, Any


def repair_pdf(pdf_data: bytes, aggressive: bool = False) -> bytes:
    """
    Attempt to repair a corrupted or damaged PDF file.

    Args:
        pdf_data: PDF file bytes
        aggressive: If True, try more aggressive repair methods

    Returns:
        Repaired PDF as bytes
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5:
        raise ValueError("Invalid PDF file - too small")

    doc = None
    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        # If we can open it, check if it has pages
        if doc.page_count == 0:
            raise ValueError("PDF has no pages")

        # Save with garbage collection to clean up
        output_buffer = io.BytesIO()
        if aggressive:
            doc.save(output_buffer, garbage=4, deflate=True, clean=True)
        else:
            doc.save(output_buffer, garbage=3, deflate=True)

        doc.close()
        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        raise RuntimeError(f"PDF repair failed: {str(e)}") from e
    finally:
        if doc is not None:
            doc.close()


def get_repair_info(pdf_data: bytes) -> dict:
    """
    Get information about PDF repair assessment.

    Args:
        pdf_data: PDF file bytes

    Returns:
        Dictionary with repair assessment information
    """
    info = {
        "is_valid_pdf": False,
        "page_count": 0,
        "file_size": len(pdf_data),
        "has_xref": False,
        "has_trailer": False,
        "can_repair": False,
        "issues": []
    }

    if not pdf_data or len(pdf_data) < 5:
        info["issues"].append("File too small to be a valid PDF")
        return info

    # Check PDF signature
    if pdf_data[:5] == b'%PDF-':
        info["is_valid_pdf"] = True

        # Check for basic PDF structure
        content = pdf_data[:min(len(pdf_data), 10000)].decode('latin-1', errors='ignore')
        if 'xref' in content.lower():
            info["has_xref"] = True
        if 'trailer' in content.lower():
            info["has_trailer"] = True

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        info["page_count"] = doc.page_count
        info["can_repair"] = True
        doc.close()
    except Exception as e:
        info["issues"].append(f"Cannot open with PyMuPDF: {str(e)}")

    if not info["has_xref"]:
        info["issues"].append("Missing xref table")
    if not info["has_trailer"]:
        info["issues"].append("Missing trailer")

    return info