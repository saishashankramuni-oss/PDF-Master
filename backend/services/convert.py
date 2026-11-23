"""
PDF Conversion Service
Handles converting PDF to/from various formats using LibreOffice and PyMuPDF.
"""

import fitz  # PyMuPDF
import io
import os
import subprocess
import tempfile
import shutil
from typing import Optional, Dict, Any, List


def pdf_to_images(pdf_data: bytes, output_format: str = "jpg", dpi: int = 150) -> List[bytes]:
    """
    Convert PDF pages to images (JPG, PNG).

    Args:
        pdf_data: PDF file bytes
        output_format: "jpg" or "png"
        dpi: Resolution for image rendering

    Returns:
        List of image bytes (one per page)
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        images = []

        for page_num in range(doc.page_count):
            page = doc[page_num]
            # Render page to pixmap
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            if output_format.lower() == "png":
                img_bytes = pix.tobytes("png")
            else:
                img_bytes = pix.tobytes("jpg")

            images.append(img_bytes)

        doc.close()
        return images

    except Exception as e:
        raise RuntimeError(f"PDF to images conversion failed: {str(e)}")


def pdf_to_word(pdf_data: bytes) -> bytes:
    """
    Convert PDF to Word document (.docx) using LibreOffice.

    Args:
        pdf_data: PDF file bytes

    Returns:
        Word document as bytes
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "input.pdf")
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir, exist_ok=True)

        # Write PDF
        with open(pdf_path, "wb") as f:
            f.write(pdf_data)

        # Convert using LibreOffice
        try:
            result = subprocess.run([
                "libreoffice",
                "--headless",
                "--convert-to", "docx",
                "--outdir", output_dir,
                pdf_path
            ], capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

            # Find output file
            docx_files = [f for f in os.listdir(output_dir) if f.endswith(".docx")]
            if not docx_files:
                raise RuntimeError("No output file generated")

            output_path = os.path.join(output_dir, docx_files[0])
            with open(output_path, "rb") as f:
                return f.read()

        except subprocess.TimeoutExpired:
            raise RuntimeError("Conversion timed out")
        except FileNotFoundError:
            # LibreOffice not available, fall back to PyMuPDF text extraction
            return _pdf_to_word_fallback(pdf_data)


def _pdf_to_word_fallback(pdf_data: bytes) -> bytes:
    """
    Fallback PDF to Word conversion using python-docx when LibreOffice is unavailable.
    Creates a basic Word document with extracted text.
    """
    try:
        from docx import Document
        import io

        doc = fitz.open(stream=pdf_data, filetype="pdf")
        word_doc = Document()

        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text("text")

            if text.strip():
                word_doc.add_paragraph(text)

            if page_num < doc.page_count - 1:
                word_doc.add_page_break()

        doc.close()

        # Save to bytes
        output_buffer = io.BytesIO()
        word_doc.save(output_buffer)
        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        raise RuntimeError(f"Fallback PDF to Word failed: {str(e)}")


def word_to_pdf(word_data: bytes) -> bytes:
    """
    Convert Word document (.docx) to PDF using LibreOffice.

    Args:
        word_data: Word document bytes

    Returns:
        PDF as bytes
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        word_path = os.path.join(tmpdir, "input.docx")
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir, exist_ok=True)

        # Write Word document
        with open(word_path, "wb") as f:
            f.write(word_data)

        # Convert using LibreOffice
        try:
            result = subprocess.run([
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", output_dir,
                word_path
            ], capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

            # Find output file
            pdf_files = [f for f in os.listdir(output_dir) if f.endswith(".pdf")]
            if not pdf_files:
                raise RuntimeError("No output file generated")

            output_path = os.path.join(output_dir, pdf_files[0])
            with open(output_path, "rb") as f:
                return f.read()

        except subprocess.TimeoutExpired:
            raise RuntimeError("Conversion timed out")
        except FileNotFoundError:
            raise RuntimeError("LibreOffice not available for Word to PDF conversion")


def images_to_pdf(image_data_list: List[bytes]) -> bytes:
    """
    Convert multiple images to a single PDF.

    Args:
        image_data_list: List of image bytes

    Returns:
        PDF as bytes
    """
    try:
        doc = fitz.open()

        for img_data in image_data_list:
            # Determine image format
            if img_data[:4] == b'\x89PNG':
                img_format = "png"
            elif img_data[:2] == b'\xFF\xD8':
                img_format = "jpg"
            else:
                # Try to open as pixmap
                img_format = "png"

            # Insert image
            page = doc.new_page()
            rect = page.rect
            page.insert_image(rect, stream=img_data)

        # Save to bytes
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()
        output_buffer.seek(0)
        return output_buffer.read()

    except Exception as e:
        raise RuntimeError(f"Images to PDF conversion failed: {str(e)}")


def pdf_to_excel(pdf_data: bytes) -> bytes:
    """
    Convert PDF to Excel (.xlsx) using LibreOffice.

    Args:
        pdf_data: PDF file bytes

    Returns:
        Excel file as bytes
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "input.pdf")
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir, exist_ok=True)

        with open(pdf_path, "wb") as f:
            f.write(pdf_data)

        try:
            result = subprocess.run([
                "libreoffice",
                "--headless",
                "--convert-to", "xlsx",
                "--outdir", output_dir,
                pdf_path
            ], capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

            xlsx_files = [f for f in os.listdir(output_dir) if f.endswith(".xlsx")]
            if not xlsx_files:
                raise RuntimeError("No output file generated")

            output_path = os.path.join(output_dir, xlsx_files[0])
            with open(output_path, "rb") as f:
                return f.read()

        except subprocess.TimeoutExpired:
            raise RuntimeError("Conversion timed out")
        except FileNotFoundError:
            raise RuntimeError("LibreOffice not available for PDF to Excel conversion")


def excel_to_pdf(excel_data: bytes) -> bytes:
    """
    Convert Excel (.xlsx) to PDF using LibreOffice.

    Args:
        excel_data: Excel file bytes

    Returns:
        PDF as bytes
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        excel_path = os.path.join(tmpdir, "input.xlsx")
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir, exist_ok=True)

        with open(excel_path, "wb") as f:
            f.write(excel_data)

        try:
            result = subprocess.run([
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", output_dir,
                excel_path
            ], capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

            pdf_files = [f for f in os.listdir(output_dir) if f.endswith(".pdf")]
            if not pdf_files:
                raise RuntimeError("No output file generated")

            output_path = os.path.join(output_dir, pdf_files[0])
            with open(output_path, "rb") as f:
                return f.read()

        except subprocess.TimeoutExpired:
            raise RuntimeError("Conversion timed out")
        except FileNotFoundError:
            raise RuntimeError("LibreOffice not available for Excel to PDF conversion")


def pdf_to_powerpoint(pdf_data: bytes) -> bytes:
    """
    Convert PDF to PowerPoint (.pptx) using LibreOffice.

    Args:
        pdf_data: PDF file bytes

    Returns:
        PowerPoint file as bytes
    """
    if not pdf_data or len(pdf_data) < 5 or pdf_data[:5] != b'%PDF-':
        raise ValueError("Invalid PDF file")

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "input.pdf")
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir, exist_ok=True)

        with open(pdf_path, "wb") as f:
            f.write(pdf_data)

        try:
            result = subprocess.run([
                "libreoffice",
                "--headless",
                "--convert-to", "pptx",
                "--outdir", output_dir,
                pdf_path
            ], capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

            pptx_files = [f for f in os.listdir(output_dir) if f.endswith(".pptx")]
            if not pptx_files:
                raise RuntimeError("No output file generated")

            output_path = os.path.join(output_dir, pptx_files[0])
            with open(output_path, "rb") as f:
                return f.read()

        except subprocess.TimeoutExpired:
            raise RuntimeError("Conversion timed out")
        except FileNotFoundError:
            raise RuntimeError("LibreOffice not available for PDF to PowerPoint conversion")


def powerpoint_to_pdf(ppt_data: bytes) -> bytes:
    """
    Convert PowerPoint (.pptx) to PDF using LibreOffice.

    Args:
        ppt_data: PowerPoint file bytes

    Returns:
        PDF as bytes
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        ppt_path = os.path.join(tmpdir, "input.pptx")
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir, exist_ok=True)

        with open(ppt_path, "wb") as f:
            f.write(ppt_data)

        try:
            result = subprocess.run([
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", output_dir,
                ppt_path
            ], capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

            pdf_files = [f for f in os.listdir(output_dir) if f.endswith(".pdf")]
            if not pdf_files:
                raise RuntimeError("No output file generated")

            output_path = os.path.join(output_dir, pdf_files[0])
            with open(output_path, "rb") as f:
                return f.read()

        except subprocess.TimeoutExpired:
            raise RuntimeError("Conversion timed out")
        except FileNotFoundError:
            raise RuntimeError("LibreOffice not available for PowerPoint to PDF conversion")


def get_convert_info(conversion_type: str, pdf_data: bytes = None) -> dict:
    """
    Get information about conversion operation.

    Args:
        conversion_type: Type of conversion
        pdf_data: Optional PDF data for analysis

    Returns:
        Dictionary with conversion information
    """
    info = {
        "conversion_type": conversion_type,
        "requires_libreoffice": conversion_type in [
            "pdf_to_word", "word_to_pdf", "pdf_to_excel",
            "excel_to_pdf", "pdf_to_powerpoint", "powerpoint_to_pdf"
        ],
        "supported_formats": {
            "pdf_to_jpg": ["jpg"],
            "pdf_to_png": ["png"],
            "pdf_to_word": ["docx"],
            "word_to_pdf": ["docx", "doc"],
            "pdf_to_excel": ["xlsx"],
            "excel_to_pdf": ["xlsx", "xls"],
            "pdf_to_powerpoint": ["pptx"],
            "powerpoint_to_pdf": ["pptx", "ppt"],
            "images_to_pdf": ["jpg", "png", "bmp", "tiff"]
        }
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