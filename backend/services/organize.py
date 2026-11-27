"""
PDF Organize Service
Handles organizing PDF pages - removing, extracting, and reordering.
"""

import fitz  # PyMuPDF
import io
from typing import List, Optional, Dict, Any


def remove_pages(pdf_data: bytes, pages_to_remove: List[int]) -> bytes:
    """
    Remove specific pages from a PDF.

    Args:
        pdf_data: PDF file bytes
        pages_to_remove: List of page numbers to remove (1-indexed)

    Returns:
        PDF with removed pages as bytes
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        total_pages = doc.page_count

        # Validate page numbers and convert to 0-indexed
        pages_to_remove_0indexed = []
        for p in pages_to_remove:
            if 1 <= p <= total_pages:
                pages_to_remove_0indexed.append(p - 1)
            else:
                raise ValueError(f"Invalid page number: {p} (PDF has {total_pages} pages)")

        # Get pages to keep (in reverse order to maintain correct indices)
        pages_to_keep = [i for i in range(total_pages) if i not in pages_to_remove_0indexed]

        if not pages_to_keep:
            raise ValueError("All pages would be removed. At least one page must remain.")

        # Create new document with kept pages
        new_doc = fitz.open()
        for page_idx in pages_to_keep:
            new_doc.insert_pdf(doc, from_page=page_idx, to_page=page_idx)

        # Save to bytes
        output_buffer = io.BytesIO()
        new_doc.save(output_buffer)
        new_doc.close()
        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        try:
            new_doc.close()
        except:
            pass
        try:
            doc.close()
        except:
            pass
        raise RuntimeError(f"PDF page removal failed: {str(e)}")


def extract_pages(pdf_data: bytes, pages_to_extract: List[int]) -> bytes:
    """
    Extract specific pages from a PDF into a new PDF.

    Args:
        pdf_data: PDF file bytes
        pages_to_extract: List of page numbers to extract (1-indexed)

    Returns:
        Extracted pages as a new PDF in bytes
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        total_pages = doc.page_count

        # Validate page numbers and convert to 0-indexed
        pages_to_extract_0indexed = []
        for p in pages_to_extract:
            if 1 <= p <= total_pages:
                pages_to_extract_0indexed.append(p - 1)
            else:
                raise ValueError(f"Invalid page number: {p} (PDF has {total_pages} pages)")

        if not pages_to_extract_0indexed:
            raise ValueError("No valid pages specified for extraction")

        # Create new document with extracted pages
        new_doc = fitz.open()
        for page_idx in pages_to_extract_0indexed:
            new_doc.insert_pdf(doc, from_page=page_idx, to_page=page_idx)

        # Save to bytes
        output_buffer = io.BytesIO()
        new_doc.save(output_buffer)
        new_doc.close()
        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        try:
            new_doc.close()
        except:
            pass
        try:
            doc.close()
        except:
            pass
        raise RuntimeError(f"PDF page extraction failed: {str(e)}")


def organize_pages(pdf_data: bytes, operation: str,
                   page_data: Dict[str, Any]) -> bytes:
    """
    Organize PDF pages based on the specified operation.

    Supported operations:
    - "reorder": Reorder pages based on new order
    - "move": Move a page to a new position
    - "copy": Copy pages to a new document

    Args:
        pdf_data: PDF file bytes
        operation: Organization operation type
        page_data: Dictionary with page operation details

    Returns:
        Organized PDF as bytes
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        total_pages = doc.page_count

        operation = operation.lower()

        if operation == "reorder":
            # Reorder pages based on new order
            new_order = page_data.get("new_order", [])
            if not new_order or len(new_order) != total_pages:
                raise ValueError(f"Invalid reorder sequence. Expected {total_pages} page numbers")

            # Validate page numbers
            valid_new_order = []
            for p in new_order:
                if 1 <= p <= total_pages and p not in valid_new_order:
                    valid_new_order.append(p)
                else:
                    raise ValueError(f"Duplicate or invalid page number: {p}")

            # Create new document with reordered pages
            new_doc = fitz.open()
            for page_num in valid_new_order:
                new_doc.insert_pdf(doc, from_page=page_num - 1, to_page=page_num - 1)

        elif operation == "move":
            # Move a page to a new position
            from_page = page_data.get("from_page", 1)
            to_page = page_data.get("to_page", 1)

            if from_page < 1 or from_page > total_pages:
                raise ValueError(f"Invalid from_page: {from_page}")
            if to_page < 1 or to_page > total_pages:
                raise ValueError(f"Invalid to_page: {to_page}")

            if from_page == to_page:
                # No movement needed, return original
                output_buffer = io.BytesIO()
                doc.save(output_buffer)
                doc.close()
                output_buffer.seek(0)
                return output_buffer.read()

            # Move the source page within its final ordering before copying pages.
            page_order = list(range(total_pages))
            moved_page = page_order.pop(from_page - 1)
            page_order.insert(to_page - 1, moved_page)
            new_doc = fitz.open()
            for page_index in page_order:
                new_doc.insert_pdf(doc, from_page=page_index, to_page=page_index)

        elif operation == "copy":
            pages_to_copy = page_data.get("pages", [])
            if not pages_to_copy:
                raise ValueError("At least one page must be selected for copying")
            if any(not isinstance(page, int) or page < 1 or page > total_pages for page in pages_to_copy):
                raise ValueError("Copy page numbers must be valid 1-based page numbers")

            new_doc = fitz.open()
            for page_num in pages_to_copy:
                new_doc.insert_pdf(doc, from_page=page_num - 1, to_page=page_num - 1)

        else:
            raise ValueError(f"Unsupported page organization operation: {operation}")

        # Save to bytes
        output_buffer = io.BytesIO()
        new_doc.save(output_buffer)
        new_doc.close()
        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        try:
            new_doc.close()
        except:
            pass
        try:
            doc.close()
        except:
            pass
        raise RuntimeError(f"PDF organization failed: {str(e)}")


def get_organize_info(pdf_data: bytes, operation: str,
                      page_data: Dict[str, Any]) -> dict:
    """
    Get information about PDF organization operation.

    Args:
        pdf_data: PDF file bytes
        operation: Organization operation type
        page_data: Dictionary with page operation details

    Returns:
        Dictionary with organization information
    """
    # Validate PDF signature
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        total_pages = doc.page_count
        doc.close()

        return {
            "total_pages": total_pages,
            "operation": operation,
            "operation_details": page_data,
            "is_valid": total_pages > 0
        }
    except Exception as e:
        raise RuntimeError(f"Failed to get organize info: {str(e)}")