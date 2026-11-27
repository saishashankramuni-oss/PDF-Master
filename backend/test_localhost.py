import io
import json
import os
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile

import fitz


BASE = os.environ.get("PDF_MASTER_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def multipart(fields, files):
    boundary = "----PDFMasterBoundary"
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(str(value).encode())
        body.extend(b"\r\n")
    for name, filename, content in files:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode())
        body.extend(b"Content-Type: application/pdf\r\n\r\n")
        body.extend(content)
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    return boundary, bytes(body)


def post_multipart_raw(path, fields=None, files=None):
    boundary, body = multipart(fields or {}, files or [])
    request = urllib.request.Request(
        BASE + path,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, response.headers, response.read()


def post_multipart(path, fields=None, files=None):
    status, _, body = post_multipart_raw(path, fields, files)
    return status, json.loads(body)


def get_response(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as response:
        return response.status, response.headers, response.read()


def get_json(path):
    status, _, body = get_response(path)
    return status, json.loads(body)


def get_download(job_id, token):
    query = urllib.parse.urlencode({"token": token})
    return get_response(f"/api/jobs/{job_id}/download?{query}")


def delete_job(job_id):
    request = urllib.request.Request(BASE + f"/api/jobs/{job_id}", method="DELETE")
    with urllib.request.urlopen(request, timeout=30) as response:
        assert response.status == 200


def create_pdf(path, text, page_count=1):
    document = fitz.open()
    for page_number in range(page_count):
        page = document.new_page()
        page.insert_text((72, 72), text if page_number == 0 else f"{text} page {page_number + 1}")
    document.save(path)
    document.close()


def assert_pdf(data, expected_pages=None):
    document = fitz.open(stream=data, filetype="pdf")
    if expected_pages is not None:
        assert document.page_count == expected_pages, document.page_count
    document.close()


def check_service_routes():
    _, root = get_json("/")
    assert root["status"] == "running", root
    assert root["docs"] == "/docs", root

    _, health = get_json("/health")
    assert health["status"] == "healthy", health

    _, headers, docs = get_response("/docs")
    assert "text/html" in headers.get("Content-Type", ""), headers
    assert b"swagger-ui" in docs.lower()

    _, openapi = get_json("/openapi.json")
    assert "/api/process/{tool}" in openapi["paths"]

    _, _, legacy_docs = get_response("/api/docs")
    assert b"swagger-ui" in legacy_docs.lower()

    request = urllib.request.Request(
        BASE + "/api/tools",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
        method="OPTIONS",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        assert response.status == 200
        assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"


def check_direct_processing(first, second):
    cases = [
        ("merge", [
            ("files", "test_sample.pdf", first),
            ("files", "test_sample_2.pdf", second),
        ], {}),
        ("split", [("files", "test_sample.pdf", first)], {}),
        ("rotate", [("files", "test_sample.pdf", first)], {"angle": "90"}),
        ("compress", [("files", "test_sample.pdf", first)], {"quality": "medium"}),
        ("extract-text", [("files", "test_sample.pdf", first)], {}),
        ("metadata", [("files", "test_sample.pdf", first)], {}),
    ]

    for tool, files, fields in cases:
        status, headers, result = post_multipart_raw(f"/api/process/{tool}", fields, files)
        assert status == 200, (tool, status, result[:300])
        content_type = headers.get_content_type()

        if tool == "split":
            assert content_type == "application/zip", content_type
            with zipfile.ZipFile(io.BytesIO(result)) as archive:
                names = archive.namelist()
                assert names == ["page-1.pdf", "page-2.pdf"], names
                for name in names:
                    assert_pdf(archive.read(name), 1)
        elif tool in {"merge", "rotate", "compress"}:
            assert content_type == "application/pdf", content_type
            expected_pages = 3 if tool == "merge" else 2
            document = fitz.open(stream=result, filetype="pdf")
            assert document.page_count == expected_pages, document.page_count
            if tool == "rotate":
                assert document[0].rotation == 90, document[0].rotation
            document.close()
        elif tool == "extract-text":
            assert content_type.startswith("text/plain"), content_type
            text = result.decode("utf-8")
            assert "PDF Master test page" in text, text
            assert "\\n" not in text, text
        else:
            assert content_type == "application/json", content_type
            metadata = json.loads(result)
            assert metadata["page_count"] == 2, metadata
        print(f"direct {tool}: PASS ({content_type}, {len(result)} bytes)")


def check_job_processing(first, second):
    tests = [
        ("merge", "/api/pdf/merge", {}, [
            ("files", "test_sample.pdf", first),
            ("files", "test_sample_2.pdf", second),
        ]),
        ("split", "/api/pdf/split", {}, [
            ("file", "test_sample.pdf", first),
        ]),
        ("rotate", "/api/pdf/rotate", {"angle": "90"}, [
            ("file", "test_sample.pdf", first),
        ]),
        ("compress", "/api/pdf/compress", {"quality": "medium"}, [
            ("file", "test_sample.pdf", first),
        ]),
        ("extract-text", "/api/pdf/extract-text", {}, [
            ("file", "test_sample.pdf", first),
        ]),
        ("metadata", "/api/pdf/metadata", {}, [
            ("file", "test_sample.pdf", first),
        ]),
        ("add-annotation", "/api/pdf/add-annotation", {
            "page_number": "1",
            "annotation_type": "highlight",
            "x0": "72",
            "y0": "72",
            "x1": "180",
            "y1": "100",
        }, [
            ("file", "test_sample.pdf", first),
        ]),
    ]

    for name, path, fields, files in tests:
        _, data = post_multipart(path, fields, files)
        job_id = data["job_id"]
        token = data.get("download_token")
        job = None
        for _ in range(40):
            _, job = get_json(f"/api/jobs/{job_id}")
            if job["status"] in ("completed", "failed"):
                break
            time.sleep(0.25)
        assert job and job["status"] == "completed", (name, job)
        token = token or job.get("download_token")
        assert token, f"{name} did not expose a download token in its job response"

        status, headers, output = get_download(job_id, token)
        assert status == 200
        content_type = headers.get_content_type()
        if name in {"merge", "rotate", "compress", "add-annotation"}:
            assert content_type == "application/pdf", (name, content_type)
            assert_pdf(output, 3 if name == "merge" else 2)
        elif name == "split":
            assert content_type == "application/zip", content_type
            with zipfile.ZipFile(io.BytesIO(output)) as archive:
                assert_pdf(archive.read("page_1.pdf"), 1)
                assert_pdf(archive.read("page_2.pdf"), 1)
        else:
            payload = json.loads(output)
            if name == "extract-text":
                assert "PDF Master test page" in payload["full_text"], payload
            else:
                assert payload["page_count"] == 2, payload
        delete_job(job_id)
        print(f"job {name}: PASS ({content_type}, {len(output)} bytes)")


def main():
    with tempfile.TemporaryDirectory(prefix="pdf-master-smoke-") as temp_dir:
        first_path = os.path.join(temp_dir, "test_sample.pdf")
        second_path = os.path.join(temp_dir, "test_sample_2.pdf")
        create_pdf(first_path, "PDF Master test page", page_count=2)
        create_pdf(second_path, "Second test page")

        with open(first_path, "rb") as file:
            first = file.read()
        with open(second_path, "rb") as file:
            second = file.read()

        check_service_routes()
        print("service routes: PASS")
        check_direct_processing(first, second)
        check_job_processing(first, second)


if __name__ == "__main__":
    main()
