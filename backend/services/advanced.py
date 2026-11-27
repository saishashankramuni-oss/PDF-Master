"""
Advanced PDF Tools Service
Handles OCR, Redaction, Compare, Extract Text/Images, Metadata, Page Preview.
"""

import fitz  # PyMuPDF
import io
from typing import Dict, Any, List
import base64


def _load_tesseract():
    try:
        import pytesseract
        from PIL import Image
        pytesseract.get_tesseract_version()
    except Exception as exc:
        raise RuntimeError(
            "Tesseract OCR is unavailable. Install Tesseract and the requested language data."
        ) from exc
    return pytesseract, Image


def ocr_pdf(
    pdf_data: bytes,
    language: str = "eng",
    dpi: int = 300
) -> bytes:
    """
    Perform OCR on scanned PDF pages and add recognized text as an invisible layer.

    Args:
        pdf_data: PDF file bytes
        language: OCR language code (eng, spa, fra, etc.)
        dpi: Resolution for OCR processing

    Returns:
        OCR-processed PDF as bytes
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")
    if not language.strip():
        raise ValueError("OCR language must not be empty")
    if not 72 <= dpi <= 600:
        raise ValueError("OCR resolution must be between 72 and 600 DPI")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        tesseract = None
        image_class = None
        scanned_pages = 0
        recognized_pages = 0

        for page_num in range(doc.page_count):
            page = doc[page_num]
            if page.get_text("text").strip():
                continue

            if tesseract is None:
                tesseract, image_class = _load_tesseract()

            scanned_pages += 1
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
            image = image_class.frombytes("RGB", [pix.width, pix.height], pix.samples)
            try:
                ocr_text = tesseract.image_to_string(image, lang=language).strip()
            except Exception as exc:
                raise RuntimeError(f"OCR failed on page {page_num + 1}: {exc}") from exc

            if not ocr_text:
                continue

            remaining_height = page.insert_textbox(
                page.rect,
                ocr_text,
                fontsize=1,
                fontname="helv",
                render_mode=3,
            )
            if remaining_height < 0:
                raise RuntimeError(
                    f"OCR text from page {page_num + 1} exceeds the available page area."
                )
            recognized_pages += 1

        if scanned_pages and not recognized_pages:
            raise RuntimeError("OCR did not recognize readable text in the scanned pages.")

        return doc.tobytes(garbage=4, deflate=True)
    except Exception as exc:
        if isinstance(exc, (ValueError, RuntimeError)):
            raise
        raise RuntimeError(f"OCR failed: {exc}") from exc
    finally:
        if "doc" in locals():
            doc.close()


def redact_pdf(
    pdf_data: bytes,
    redactions: List[Dict[str, Any]]
) -> bytes:
    """
    Redact (permanently remove) content from PDF pages.

    Args:
        pdf_data: PDF file bytes
        redactions: List of redaction specs with keys:
            - page: Page number (1-indexed)
            - x0, y0, x1, y1: Rectangle coordinates
            - fill_color: RGB tuple for redaction fill (default black)

    Returns:
        Redacted PDF as bytes
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        for redact in redactions:
            page_num = redact.get("page", 1)
            if page_num < 1 or page_num > doc.page_count:
                continue

            page = doc[page_num - 1]

            # Create redaction rectangle
            rect = fitz.Rect(
                redact.get("x0", 0),
                redact.get("y0", 0),
                redact.get("x1", 100),
                redact.get("y1", 100)
            )

            # Add redaction annotation
            annot = page.add_redact_annot(rect)

            # Set fill color
            fill = redact.get("fill_color", (0, 0, 0))
            annot.set_colors(stroke=fill, fill=fill)

        # Apply redactions
        for page_num in range(doc.page_count):
            page = doc[page_num]
            page.apply_redactions()

        # Save to bytes
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        raise RuntimeError(f"Redaction failed: {str(e)}")


def compare_pdfs(
    pdf_data1: bytes,
    pdf_data2: bytes,
    diff_mode: str = "text"
) -> Dict[str, Any]:
    """
    Compare two PDFs and return differences.

    Args:
        pdf_data1: First PDF file bytes
        pdf_data2: Second PDF file bytes
        diff_mode: "text" or "visual"

    Returns:
        Dictionary with comparison results
    """
    if not pdf_data1 or len(pdf_data1) < 5 or pdf_data1[:5] != b'%PDF-':
        raise ValueError("Invalid first PDF file")
    if not pdf_data2 or len(pdf_data2) < 5 or pdf_data2[:5] != b'%PDF-':
        raise ValueError("Invalid second PDF file")

    try:
        doc1 = fitz.open(stream=pdf_data1, filetype="pdf")
        doc2 = fitz.open(stream=pdf_data2, filetype="pdf")

        result = {
            "page_count_1": doc1.page_count,
            "page_count_2": doc2.page_count,
            "pages_match": doc1.page_count == doc2.page_count,
            "differences": []
        }

        max_pages = max(doc1.page_count, doc2.page_count)

        for i in range(max_pages):
            page_diff = {"page": i + 1, "changes": []}

            text1 = ""
            text2 = ""

            if i < doc1.page_count:
                text1 = doc1[i].get_text("text")

            if i < doc2.page_count:
                text2 = doc2[i].get_text("text")

            if text1 != text2:
                page_diff["changes"].append({
                    "type": "text",
                    "original": text1[:500] if text1 else "",
                    "modified": text2[:500] if text2 else ""
                })

            if page_diff["changes"]:
                result["differences"].append(page_diff)

        doc1.close()
        doc2.close()

        return result

    except Exception as e:
        raise RuntimeError(f"PDF comparison failed: {str(e)}")


def extract_text(pdf_data: bytes) -> Dict[str, Any]:
    """
    Extract all text content from a PDF.

    Args:
        pdf_data: PDF file bytes

    Returns:
        Dictionary with extracted text by page and full text
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        result = {
            "page_count": doc.page_count,
            "pages": [],
            "full_text": ""
        }

        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text("text")

            page_info = {
                "page": page_num + 1,
                "text": text,
                "char_count": len(text),
                "word_count": len(text.split()) if text else 0
            }

            result["pages"].append(page_info)
            result["full_text"] += f"\n--- Page {page_num + 1} ---\n{text}"

        doc.close()
        return result

    except Exception as e:
        raise RuntimeError(f"Text extraction failed: {str(e)}")


def extract_images(pdf_data: bytes) -> List[Dict[str, Any]]:
    """
    Extract all images from a PDF.

    Args:
        pdf_data: PDF file bytes

    Returns:
        List of image info with base64 encoded data
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        images = []

        for page_num in range(doc.page_count):
            page = doc[page_num]
            image_list = page.get_images(full=True)

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)

                if base_image:
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    width = base_image["width"]
                    height = base_image["height"]

                    # Encode to base64
                    b64_data = base64.b64encode(image_bytes).decode('utf-8')

                    images.append({
                        "page": page_num + 1,
                        "index": img_index,
                        "format": image_ext,
                        "width": width,
                        "height": height,
                        "size": len(image_bytes),
                        "data_base64": b64_data
                    })

        doc.close()
        return images

    except Exception as e:
        raise RuntimeError(f"Image extraction failed: {str(e)}")


def get_pdf_metadata(pdf_data: bytes) -> Dict[str, Any]:
    """
    Get comprehensive PDF metadata.

    Args:
        pdf_data: PDF file bytes

    Returns:
        Dictionary with metadata
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        meta = doc.metadata

        # Get additional info
        info = {
            "page_count": doc.page_count,
            "file_size": len(pdf_data),
            "is_encrypted": doc.is_encrypted,
            "is_pdf": True,
            "pdf_version": f"{doc.pdf_version()}" if hasattr(doc, 'pdf_version') else "Unknown",
            "metadata": meta,
            "pages_info": []
        }

        # Get page details
        for page_num in range(doc.page_count):
            page = doc[page_num]
            rect = page.rect
            info["pages_info"].append({
                "page": page_num + 1,
                "width": rect.width,
                "height": rect.height,
                "rotation": page.rotation
            })

        doc.close()
        return info

    except Exception as e:
        raise RuntimeError(f"Metadata extraction failed: {str(e)}")


def generate_page_previews(pdf_data: bytes, dpi: int = 96, max_pages: int = 20) -> List[Dict[str, Any]]:
    """
    Generate page preview thumbnails.

    Args:
        pdf_data: PDF file bytes
        dpi: Resolution for preview
        max_pages: Maximum pages to preview

    Returns:
        List of page preview info with base64 encoded thumbnails
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        previews = []

        pages_to_preview = min(doc.page_count, max_pages)

        for page_num in range(pages_to_preview):
            page = doc[page_num]

            # Render page to pixmap
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            # Convert to PNG bytes
            img_bytes = pix.tobytes("png")

            # Encode to base64
            b64_data = base64.b64encode(img_bytes).decode('utf-8')

            previews.append({
                "page": page_num + 1,
                "format": "png",
                "width": pix.width,
                "height": pix.height,
                "data_base64": b64_data
            })

        doc.close()
        return previews

    except Exception as e:
        raise RuntimeError(f"Preview generation failed: {str(e)}")


def get_advanced_info(pdf_data: bytes, operation: str, **kwargs) -> dict:
    """
    Get information about an advanced operation.

    Args:
        pdf_data: PDF file bytes
        operation: Operation type
        **kwargs: Operation parameters

    Returns:
        Dictionary with operation information
    """
    info = {
        "operation": operation,
        "requires_pdf": True,
        "parameters": kwargs
    }

    if pdf_data and pdf_data[:5] == b'%PDF-':
        try:
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            info["page_count"] = doc.page_count
            info["file_size"] = len(pdf_data)
            doc.close()
        except:
            pass

    return info