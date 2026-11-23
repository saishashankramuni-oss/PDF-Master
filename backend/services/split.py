"""
PDF Split Service
Handles splitting PDF files into individual pages or page ranges.
"""

import fitz  # PyMuPDF
import io
from typing import List, Tuple


def split_pdf(pdf_data: bytes, page_numbers: List[int] = None,
              all_pages: bool = False) -> List[bytes]:
    """
    Split a PDF file into individual pages or selected page ranges.

    Args:
        pdf_data: PDF file bytes
        page_numbers: List of page numbers to extract (1-indexed).
                     If None and all_pages is False, returns all pages individually.
        all_pages: If True, extract all pages as individual PDFs.

    Returns:
        List of PDF bytes, each containing the selected pages
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        total_pages = doc.page_count

        # Determine which pages to extract
        if all_pages or page_numbers is None:
            # Extract all pages individually
            page_range = range(1, total_pages + 1)
        else:
            # Validate page numbers
            page_range = []
            for p in page_numbers:
                if 1 <= p <= total_pages:
                    page_range.append(p)
                else:
                    raise ValueError(f"Invalid page number: {p} (PDF has {total_pages} pages)")

        results = []

        for page_num in page_range:
            # Create new document with just this page
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=page_num - 1, to_page=page_num - 1)

            # Save to bytes
            output_buffer = io.BytesIO()
            new_doc.save(output_buffer)
            new_doc.close()

            output_buffer.seek(0)
            results.append(output_buffer.read())

        doc.close()  # Close original doc after all pages processed
        return results

    except Exception as e:
        raise RuntimeError(f"PDF split failed: {str(e)}")


def get_split_info(pdf_data: bytes, page_numbers: List[int] = None,
                   all_pages: bool = False) -> dict:
    """
    Get information about PDF splitting operation.

    Args:
        pdf_data: PDF file bytes
        page_numbers: List of page numbers to extract
        all_pages: If True, extract all pages

    Returns:
        Dictionary with split information
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        total_pages = doc.page_count

        if all_pages or page_numbers is None:
            page_count = total_pages
            operation = "all pages"
        else:
            # Filter valid page numbers
            valid_pages = [p for p in page_numbers if 1 <= p <= total_pages]
            page_count = len(valid_pages)
            operation = f"{page_count} selected pages"

        doc.close()

        return {
            "total_pages_in_input": total_pages,
            "pages_to_extract": page_count,
            "operation": operation,
            "output_format": "individual PDFs"
        }
    except Exception as e:
        raise RuntimeError(f"Failed to get split info: {str(e)}")