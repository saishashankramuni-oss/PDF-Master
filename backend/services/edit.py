"""
PDF Edit Service
Handles editing PDF files - adding text, images, watermarks, page numbers, signatures, annotations.
"""

import fitz  # PyMuPDF
import io
from typing import Optional, Dict, Any, List, Tuple


def add_text_to_pdf(
    pdf_data: bytes,
    page_number: int,
    x: float,
    y: float,
    text: str,
    font_size: float = 12,
    font_name: str = "helv",
    color: Tuple[float, float, float] = (0, 0, 0),
    rotation: float = 0
) -> bytes:
    """
    Add text to a specific page of a PDF.

    Args:
        pdf_data: PDF file bytes
        page_number: Page number (1-indexed)
        x: X coordinate (points from left)
        y: Y coordinate (points from top)
        text: Text to add
        font_size: Font size in points
        font_name: Font name (helv, tiro, cour, symb, etc.)
        color: RGB color tuple (0-1 range)
        rotation: Text rotation in degrees

    Returns:
        Modified PDF as bytes
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        if page_number < 1 or page_number > doc.page_count:
            raise ValueError(f"Invalid page number: {page_number} (PDF has {doc.page_count} pages)")

        page = doc[page_number - 1]

        # Insert text
        page.insert_text(
            (x, y),
            text,
            fontsize=font_size,
            fontname=font_name,
            color=color,
            rotate=rotation
        )

        # Save to bytes
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        raise RuntimeError(f"Add text failed: {str(e)}")


def add_image_to_pdf(
    pdf_data: bytes,
    page_number: int,
    x: float,
    y: float,
    image_data: bytes,
    width: Optional[float] = None,
    height: Optional[float] = None,
    keep_aspect_ratio: bool = True
) -> bytes:
    """
    Add an image to a specific page of a PDF.

    Args:
        pdf_data: PDF file bytes
        page_number: Page number (1-indexed)
        x: X coordinate (points from left)
        y: Y coordinate (points from top)
        image_data: Image file bytes
        width: Desired width in points
        height: Desired height in points
        keep_aspect_ratio: Maintain aspect ratio

    Returns:
        Modified PDF as bytes
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    if not image_data:
        raise ValueError("No image data provided")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        if page_number < 1 or page_number > doc.page_count:
            raise ValueError(f"Invalid page number: {page_number} (PDF has {doc.page_count} pages)")

        page = doc[page_number - 1]

        # Get image dimensions
        pix = fitz.Pixmap(image_data)
        img_width = pix.width
        img_height = pix.height

        # Calculate dimensions
        if width and height:
            rect_width = width
            rect_height = height
        elif width:
            rect_width = width
            rect_height = (img_height / img_width) * width if keep_aspect_ratio else img_height
        elif height:
            rect_height = height
            rect_width = (img_width / img_height) * height if keep_aspect_ratio else img_width
        else:
            # Default: use image size but cap at page size
            page_rect = page.rect
            max_w = page_rect.width * 0.8
            max_h = page_rect.height * 0.8
            scale = min(max_w / img_width, max_h / img_height)
            rect_width = img_width * scale
            rect_height = img_height * scale

        # Create rectangle
        rect = fitz.Rect(x, y, x + rect_width, y + rect_height)

        # Insert image
        page.insert_image(rect, stream=image_data)

        # Save to bytes
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        raise RuntimeError(f"Add image failed: {str(e)}")


def add_watermark_to_pdf(
    pdf_data: bytes,
    watermark_text: str = "CONFIDENTIAL",
    font_size: float = 48,
    color: Tuple[float, float, float] = (0.5, 0.5, 0.5),
    opacity: float = 0.3,
    rotation: float = 45,
    pages: Optional[List[int]] = None
) -> bytes:
    """
    Add a text watermark to PDF pages.

    Args:
        pdf_data: PDF file bytes
        watermark_text: Watermark text
        font_size: Font size
        color: RGB color tuple (0-1 range)
        opacity: Opacity (0-1)
        rotation: Rotation angle in degrees
        pages: List of page numbers to watermark (None = all pages)

    Returns:
        Watermarked PDF as bytes
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        # Determine pages to watermark
        if pages is None:
            pages_to_watermark = range(1, doc.page_count + 1)
        else:
            pages_to_watermark = [p for p in pages if 1 <= p <= doc.page_count]

        for page_num in pages_to_watermark:
            page = doc[page_num - 1]
            page_rect = page.rect

            # Calculate center position
            center_x = page_rect.width / 2
            center_y = page_rect.height / 2

            # Create a text watermark using a Form XObject for transparency
            # We'll use a simpler approach with insert_text and adjust color for opacity
            adjusted_color = (
                color[0] * opacity,
                color[1] * opacity,
                color[2] * opacity
            )

            # Add watermark text (simple approach - just draw text at center with rotation)
            # Note: PyMuPDF rotation is limited, so we use a simple center placement
            page.insert_text(
                (center_x, center_y),
                watermark_text,
                fontsize=font_size,
                fontname="helv",
                color=adjusted_color,
                rotate=rotation if rotation in [0, 90, 180, 270] else 0
            )

        # Save to bytes
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        raise RuntimeError(f"Add watermark failed: {str(e)}")


def add_page_numbers_to_pdf(
    pdf_data: bytes,
    start_number: int = 1,
    format_string: str = "{page}/{total}",
    position: str = "bottom-center",
    font_size: float = 10,
    font_name: str = "helv",
    color: Tuple[float, float, float] = (0.3, 0.3, 0.3),
    pages: Optional[List[int]] = None
) -> bytes:
    """
    Add page numbers to PDF pages.

    Args:
        pdf_data: PDF file bytes
        start_number: Starting page number
        format_string: Format string with {page} and {total} placeholders
        position: Position (bottom-center, bottom-left, bottom-right, top-center, top-left, top-right)
        font_size: Font size
        font_name: Font name
        color: RGB color tuple
        pages: List of page numbers (None = all pages)

    Returns:
        PDF with page numbers as bytes
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        total_pages = doc.page_count

        if pages is None:
            pages_to_number = range(1, total_pages + 1)
        else:
            pages_to_number = [p for p in pages if 1 <= p <= total_pages]

        for i, page_num in enumerate(pages_to_number):
            page = doc[page_num - 1]
            page_rect = page.rect

            # Calculate page number
            current_page = start_number + i

            # Format page number text
            page_text = format_string.replace("{page}", str(current_page)).replace("{total}", str(total_pages))

            # Calculate position
            text_width = fitz.get_text_length(page_text, fontname=font_name, fontsize=font_size)
            margin = 36  # 0.5 inch margin

            if "left" in position:
                x = margin
            elif "right" in position:
                x = page_rect.width - text_width - margin
            else:  # center
                x = (page_rect.width - text_width) / 2

            if "top" in position:
                y = margin + font_size
            else:  # bottom
                y = page_rect.height - margin

            # Insert page number
            page.insert_text(
                (x, y),
                page_text,
                fontsize=font_size,
                fontname=font_name,
                color=color
            )

        # Save to bytes
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        raise RuntimeError(f"Add page numbers failed: {str(e)}")


def add_signature_to_pdf(
    pdf_data: bytes,
    page_number: int,
    x: float,
    y: float,
    signature_image: bytes,
    width: float = 150,
    height: float = 75
) -> bytes:
    """
    Add a signature image to a PDF.

    Args:
        pdf_data: PDF file bytes
        page_number: Page number (1-indexed)
        x: X coordinate
        y: Y coordinate
        signature_image: Signature image bytes
        width: Signature width
        height: Signature height

    Returns:
        Signed PDF as bytes
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    if not signature_image:
        raise ValueError("No signature image provided")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        if page_number < 1 or page_number > doc.page_count:
            raise ValueError(f"Invalid page number: {page_number} (PDF has {doc.page_count} pages)")

        page = doc[page_number - 1]

        # Create rectangle for signature
        rect = fitz.Rect(x, y, x + width, y + height)

        # Insert signature image
        page.insert_image(rect, stream=signature_image)

        # Save to bytes
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        raise RuntimeError(f"Add signature failed: {str(e)}")


def add_annotation_to_pdf(
    pdf_data: bytes,
    page_number: int,
    annotation_type: str,
    rect: Tuple[float, float, float, float],
    content: str = "",
    color: Tuple[float, float, float] = (1, 1, 0),
    opacity: float = 0.5
) -> bytes:
    """
    Add an annotation to a PDF page.

    Args:
        pdf_data: PDF file bytes
        page_number: Page number (1-indexed)
        annotation_type: Type (highlight, underline, strikeout, squiggly, free_text, square, circle, line)
        rect: Rectangle (x0, y0, x1, y1)
        content: Text content for free text annotations
        color: RGB color tuple
        opacity: Opacity (0-1)

    Returns:
        Annotated PDF as bytes
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")

        if page_number < 1 or page_number > doc.page_count:
            raise ValueError(f"Invalid page number: {page_number} (PDF has {doc.page_count} pages)")

        page = doc[page_number - 1]
        annot_rect = fitz.Rect(*rect)

        annotation_type = annotation_type.lower()

        if annotation_type == "highlight":
            annot = page.add_highlight_annot(annot_rect)
        elif annotation_type == "underline":
            annot = page.add_underline_annot(annot_rect)
        elif annotation_type == "strikeout":
            annot = page.add_strikeout_annot(annot_rect)
        elif annotation_type == "squiggly":
            annot = page.add_squiggly_annot(annot_rect)
        elif annotation_type == "free_text":
            annot = page.add_freetext_annot(annot_rect, content, font_size=12)
        elif annotation_type == "square":
            annot = page.add_square_annot(annot_rect)
        elif annotation_type == "circle":
            annot = page.add_circle_annot(annot_rect)
        elif annotation_type == "line":
            annot = page.add_line_annot(annot_rect.tl, annot_rect.br)
        else:
            # Default to highlight
            annot = page.add_highlight_annot(annot_rect)

        if annot:
            annot.set_colors(stroke=color)
            annot.set_opacity(opacity)
            annot.update()

        # Save to bytes
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()

        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        raise RuntimeError(f"Add annotation failed: {str(e)}")


def get_edit_info(pdf_data: bytes, operation: str, **kwargs) -> dict:
    """
    Get information about an edit operation.

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