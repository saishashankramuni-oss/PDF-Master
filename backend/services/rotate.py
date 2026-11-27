"""
PDF Rotate Service
Handles rotating PDF pages.
"""

import fitz  # PyMuPDF
import io
from typing import List, Optional


def rotate_pdf(pdf_data: bytes, angle: float = 90) -> bytes:
    """
    Rotate all pages in a PDF by a specified angle.

    Args:
        pdf_data: PDF file bytes
        angle: Rotation angle in degrees (90, 180, 270, or any value)

    Returns:
        Rotated PDF as bytes
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    # Normalize angle to valid values
    angle = int(round(float(angle))) % 360
    if angle not in [90, 180, 270, 0]:
        # For arbitrary angles, PyMuPDF supports them but may affect rendering
        pass

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        for page_num in range(doc.page_count):
            doc[page_num].set_rotation(angle)

        # Save to bytes
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
        raise RuntimeError(f"PDF rotate failed: {str(e)}")


def get_rotate_info(pdf_data: bytes, angle: float = 90) -> dict:
    """
    Get information about PDF rotation.

    Args:
        pdf_data: PDF file bytes
        angle: Rotation angle

    Returns:
        Dictionary with rotation information
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        page_count = doc.page_count
        doc.close()

        # Normalize angle description
        angle_normalized = angle % 360
        angle_names = {0: "0° (no rotation)", 90: "90° clockwise", 180: "180°", 270: "270° clockwise"}

        return {
            "total_pages": page_count,
            "rotation_angle": angle,
            "angle_description": angle_names.get(angle_normalized, f"{angle}°"),
            "will_affect": "all pages"
        }
    except Exception as e:
        raise RuntimeError(f"Failed to get rotate info: {str(e)}")