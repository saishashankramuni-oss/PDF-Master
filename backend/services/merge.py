"""
PDF Merge Service
Handles merging multiple PDF files into one.
"""

import fitz  # PyMuPDF
import io
from typing import List


def merge_pdfs(pdf_data_list: List[bytes]) -> bytes:
    """
    Merge multiple PDF files into a single PDF.

    Args:
        pdf_data_list: List of PDF file bytes

    Returns:
        Merged PDF as bytes
    """
    if not pdf_data_list:
        raise ValueError("No PDF files provided for merging")

    if len(pdf_data_list) == 1:
        return pdf_data_list[0]

    try:
        doc = fitz.open()

        for pdf_data in pdf_data_list:
            # Validate PDF signature
            if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
                raise ValueError("Invalid PDF file in merge request")

            # Insert pages from this PDF
            temp_doc = fitz.open(stream=pdf_data, filetype="pdf")
            if temp_doc.page_count > 0:
                doc.insert_pdf(temp_doc)

        # Save to bytes
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        # Clean up if doc was opened
        try:
            doc.close()
        except:
            pass
        raise RuntimeError(f"PDF merge failed: {str(e)}")


def get_merge_info(pdf_data_list: List[bytes]) -> dict:
    """
    Get information about PDFs to be merged.

    Args:
        pdf_data_list: List of PDF file bytes

    Returns:
        Dictionary with merge information
    """
    info = {
        "total_files": len(pdf_data_list),
        "total_pages": 0,
        "file_sizes": []
    }

    for pdf_data in pdf_data_list:
        if pdf_data and len(pdf_data) >= 5 and pdf_data[:5] == b'%PDF-':
            try:
                temp_doc = fitz.open(stream=pdf_data, filetype="pdf")
                info["total_pages"] += temp_doc.page_count
                temp_doc.close()
                info["file_sizes"].append(len(pdf_data))
            except:
                info["file_sizes"].append(len(pdf_data) if pdf_data else 0)
        else:
            info["file_sizes"].append(len(pdf_data) if pdf_data else 0)

    return info