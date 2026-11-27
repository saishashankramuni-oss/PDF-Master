import fitz
import json
import os
import time
import urllib.parse
import urllib.request
from http import HTTPStatus


BASE = "http://127.0.0.1:8000"


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


def post_multipart(path, fields=None, files=None):
    boundary, body = multipart(fields or {}, files or [])
    request = urllib.request.Request(
        BASE + path,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, json.loads(response.read())


def get_json(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as response:
        return response.status, json.loads(response.read())


def get_download(job_id, token):
    url = f"{BASE}/api/jobs/{job_id}/download?{urllib.parse.urlencode({'token': token})}"
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.status, response.headers, response.read()


def create_pdf(path, text):
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def main():
    create_pdf("test_sample.pdf", "PDF Master test page")
    create_pdf("test_sample_2.pdf", "Second test page")

    first = open("test_sample.pdf", "rb").read()
    second = open("test_sample_2.pdf", "rb").read()
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
    ]

    _, health = get_json("/health")
    print("health:", health["status"])
    failed = []

    for name, path, fields, files in tests:
        try:
            status, data = post_multipart(path, fields, files)
            job_id = data["job_id"]
            token = data.get("download_token")
            for _ in range(40):
                _, job = get_json(f"/api/jobs/{job_id}")
                if job["status"] in ("completed", "failed"):
                    break
                time.sleep(0.25)
            print(name, "job:", job["status"], job.get("error_message") or "")
            if job["status"] != "completed":
                failed.append(name)
                continue
            if name == "extract-text":
                print(name, "text endpoint completed")
                continue
            status, headers, output = get_download(job_id, token)
            suffix = ".zip" if headers.get_content_type() == "application/zip" else ".pdf"
            output_path = f"test_output_{name}{suffix}"
            open(output_path, "wb").write(output)
            if suffix == ".pdf":
                document = fitz.open(output_path)
                print(name, "download:", status, "pages:", document.page_count)
                document.close()
            else:
                print(name, "download:", status, "bytes:", len(output))
        except Exception as exc:
            print(name, "FAIL:", exc)
            failed.append(name)

    if failed:
        raise SystemExit("FAILED: " + ", ".join(failed))


if __name__ == "__main__":
    main()
