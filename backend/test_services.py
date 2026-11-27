import os
import tempfile
import unittest
import zipfile
from unittest.mock import Mock, patch

import fitz
from PIL import Image

from services.advanced import ocr_pdf
from services.compress import compress_pdf, get_compress_info
from services.edit import add_annotation_to_pdf
from services.organize import organize_pages
from services.repair import repair_pdf
from main import _find_job_output


def create_pdf(page_texts):
    document = fitz.open()
    for text in page_texts:
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text)
    result = document.tobytes()
    document.close()
    return result


class PdfServiceTests(unittest.TestCase):
    def test_move_pages_preserves_requested_order(self):
        source = create_pdf(["first", "second", "third"])
        result = fitz.open(
            stream=organize_pages(source, "move", {"from_page": 3, "to_page": 1}),
            filetype="pdf",
        )
        self.addCleanup(result.close)

        self.assertEqual(
            [result[index].get_text().strip() for index in range(result.page_count)],
            ["third", "first", "second"],
        )

    def test_organize_rejects_unknown_operations(self):
        with self.assertRaisesRegex(RuntimeError, "Unsupported page organization operation"):
            organize_pages(create_pdf(["page"]), "unknown", {})

    def test_compress_info_reports_measured_output_size(self):
        source = create_pdf(["sample page"])
        info = get_compress_info(source, quality="medium")

        self.assertEqual(info["compressed_size"], len(compress_pdf(source, "medium")))
        self.assertEqual(
            info["savings_percent"],
            round((len(source) - info["compressed_size"]) / len(source) * 100, 2),
        )
        self.assertNotIn("estimated_compressed_size", info)

    def test_compress_rejects_unknown_quality(self):
        with self.assertRaisesRegex(ValueError, "quality must be"):
            compress_pdf(create_pdf(["page"]), quality="invalid")

    def test_ocr_adds_only_recognized_text(self):
        source = create_pdf([""])
        tesseract = Mock()
        tesseract.image_to_string.return_value = "recognized text"
        with patch("services.advanced._load_tesseract", return_value=(tesseract, Image)):
            result = fitz.open(stream=ocr_pdf(source), filetype="pdf")
        self.addCleanup(result.close)

        self.assertIn("recognized text", result[0].get_text())

    def test_ocr_reports_missing_tesseract_instead_of_faking_success(self):
        source = create_pdf([""])
        with patch(
            "services.advanced._load_tesseract",
            side_effect=RuntimeError("Tesseract OCR is unavailable"),
        ):
            with self.assertRaisesRegex(RuntimeError, "Tesseract OCR is unavailable"):
                ocr_pdf(source)

    def test_aggressive_repair_does_not_return_unrepaired_bytes(self):
        invalid_pdf = b"not a valid PDF document"
        with self.assertRaisesRegex(RuntimeError, "PDF repair failed"):
            repair_pdf(invalid_pdf, aggressive=True)

    def test_annotation_rejects_unknown_types(self):
        with self.assertRaisesRegex(RuntimeError, "Unsupported annotation type"):
            add_annotation_to_pdf(create_pdf(["page"]), 1, "unknown", (0, 0, 10, 10))


class JobOutputPathTests(unittest.TestCase):
    def test_named_archive_is_returned_instead_of_an_individual_split_pdf(self):
        job_id = "test-job"
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = os.path.join(temp_dir, "jobs")
            job_dir = os.path.join(jobs_dir, job_id)
            os.makedirs(job_dir)
            pdf_path = os.path.join(job_dir, "split_1.pdf")
            archive_path = os.path.join(job_dir, "split_pages.zip")
            with open(pdf_path, "wb") as file:
                file.write(b"%PDF-1.7")
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("page_1.pdf", b"%PDF-1.7")

            with patch("main.JOBS_DIR", jobs_dir):
                result = _find_job_output(job_id, "split_pages.zip")

            self.assertEqual(result, archive_path)


if __name__ == "__main__":
    unittest.main()
