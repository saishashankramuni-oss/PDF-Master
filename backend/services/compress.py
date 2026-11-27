"""
PDF Compress Service
Handles PDF compression to reduce file size.
"""

import fitz  # PyMuPDF
import io
from typing import Optional


def compress_pdf(pdf_data: bytes, quality: str = "medium",
                 target_size_kb: Optional[int] = None) -> bytes:
    """
    Compress a PDF file to reduce its size.

    Args:
        pdf_data: PDF file bytes
        quality: Compression quality ("low", "medium", "high")
        target_size_kb: Target size in KB (optional)

    Returns:
        Compressed PDF as bytes
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    # Normalize quality
    quality = quality.lower()
    if quality not in ["low", "medium", "high"]:
        raise ValueError("Compression quality must be low, medium, or high")
    if target_size_kb is not None and target_size_kb <= 0:
        raise ValueError("Target size must be a positive number of kilobytes")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        # Get original size
        original_size = len(pdf_data)

        # Save with compression using garbage collection and deflate
        # PyMuPDF uses garbage=4 for maximum compression
        output_buffer = io.BytesIO()

        # Different save options based on quality
        if quality == "high":
            doc.save(output_buffer, garbage=4, deflate=True, clean=True)
        elif quality == "medium":
            doc.save(output_buffer, garbage=3, deflate=True)
        else:  # low
            doc.save(output_buffer, garbage=1, deflate=False)

        # If target size specified and not achieved, try with higher quality
        if target_size_kb and len(output_buffer.getvalue()) > target_size_kb * 1024:
            # Try with high compression
            doc2 = fitz.open(stream=pdf_data, filetype="pdf")
            output_buffer2 = io.BytesIO()
            doc2.save(output_buffer2, garbage=4, deflate=True, clean=True)
            doc2.close()
            doc.close()
            return output_buffer2.getvalue()

        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        try:
            doc.close()
        except:
            pass
        raise RuntimeError(f"PDF compression failed: {str(e)}")


def get_compress_info(pdf_data: bytes, quality: str = "medium",
                     target_size_kb: Optional[int] = None) -> dict:
    """
    Get information about PDF compression.

    Args:
        pdf_data: PDF file bytes
        quality: Compression quality
        target_size_kb: Target size in KB

    Returns:
        Dictionary with compression information
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    doc = None
    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        page_count = doc.page_count
        original_size = len(pdf_data)
        compressed_size = len(compress_pdf(pdf_data, quality, target_size_kb))

        quality_names = {"low": "Low (minimal compression)", "medium": "Medium (balanced)", "high": "High (maximum)"}

        return {
            "original_size": original_size,
            "original_size_mb": round(original_size / (1024 * 1024), 2),
            "compressed_size": compressed_size,
            "compressed_size_mb": round(compressed_size / (1024 * 1024), 2),
            "savings_bytes": original_size - compressed_size,
            "savings_percent": round((original_size - compressed_size) / original_size * 100, 2),
            "quality": quality,
            "quality_description": quality_names.get(quality, "Medium"),
            "target_size_kb": target_size_kb,
            "pages": page_count
        }
    except Exception as e:
        raise RuntimeError(f"Failed to get compress info: {str(e)}")
    finally:
        if doc is not None:
            doc.close()