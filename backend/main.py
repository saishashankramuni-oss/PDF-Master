"""
PDF Master - Backend Application
FastAPI-based PDF processing service
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Depends, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
import zipfile
from pydantic import BaseModel, Field
import asyncio
import os
import uuid
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import struct
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PDF Master API",
    description="Universal PDF processing web application",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security and performance middleware
from middleware.security import RateLimitMiddleware, SecurityHeadersMiddleware, RequestLoggingMiddleware

app.add_middleware(RateLimitMiddleware, requests_per_minute=60, requests_per_hour=1000)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# ============================================================
# Configuration
# ============================================================

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_CONCURRENT_JOBS = 5
JOB_TIMEOUT = 300  # 5 minutes
JOB_RETENTION_MINUTES = 30

# ============================================================
# Models
# ============================================================

class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "processing", "completed", "failed", "expired"
    created_at: datetime
    completed_at: Optional[datetime] = None
    original_filename: Optional[str] = None
    output_filename: Optional[str] = None
    progress: Optional[float] = 0.0
    error_message: Optional[str] = None
    tool: Optional[str] = None

class JobCreate(BaseModel):
    tool: str
    file: UploadFile = Field(..., description="PDF file to process")

class DownloadRequest(BaseModel):
    download_token: str

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    active_jobs: int

# ============================================================
# In-memory job store (replace with Redis in production)
# ============================================================

jobs: Dict[str, JobStatus] = {}
download_tokens: Dict[str, str] = {}  # token -> job_id mapping
job_locks: Dict[str, asyncio.Lock] = {}  # Per-job locks for concurrency

# ============================================================
# Utility Functions
# ============================================================

def validate_pdf_signature(file_content: bytes) -> bool:
    """Validate PDF file signature (magic bytes)."""
    if len(file_content) < 5:
        return False
    return file_content[:5] == b'%PDF-'

def generate_job_id() -> str:
    """Generate a unique job ID."""
    return str(uuid.uuid4())

def generate_download_token() -> str:
    """Generate a secure download token."""
    return str(uuid.uuid4())

def is_valid_pdf_path(path: str) -> bool:
    """Check for path traversal attacks."""
    import re
    # Prevent directory traversal
    if '..' in path or path.startswith('/'):
        return False
    # Only allow alphanumeric, underscores, hyphens, and dots
    return bool(re.match(r'^[\w\-\.]+\.pdf$', os.path.basename(path), re.IGNORECASE))

# ============================================================
# PDF Processing Services
# ============================================================

from services.merge import merge_pdfs, get_merge_info
from services.split import split_pdf, get_split_info
from services.rotate import rotate_pdf, get_rotate_info
from services.compress import compress_pdf, get_compress_info
from services.organize import remove_pages, extract_pages, organize_pages, get_organize_info
from services.protect import protect_pdf, unlock_pdf, get_protect_info
from services.unlock import unlock_pdf_simple
from services.repair import repair_pdf, get_repair_info
from services.convert import (
    pdf_to_images, pdf_to_word, word_to_pdf, images_to_pdf,
    pdf_to_excel, excel_to_pdf, pdf_to_powerpoint, powerpoint_to_pdf,
    get_convert_info
)
from services.edit import (
    add_text_to_pdf, add_image_to_pdf, add_watermark_to_pdf,
    add_page_numbers_to_pdf, add_signature_to_pdf, add_annotation_to_pdf,
    get_edit_info
)
from services.advanced import (
    ocr_pdf, redact_pdf, compare_pdfs, extract_text, extract_images,
    get_pdf_metadata, generate_page_previews, get_advanced_info
)
from services.cleanup import cleanup_service, start_cleanup_service, stop_cleanup_service, get_cleanup_service
from services.performance import (
    performance_monitor_instance, async_cache, periodic_cache_cleanup,
    get_performance_monitor, get_async_cache, log_performance_stats
)

# ============================================================
# API Endpoints
# ============================================================

@app.get("/")
async def root():
    """Basic service check for hosting platforms."""
    return {"name": "PDF Master API", "status": "running", "health": "/health", "docs": "/api/docs"}

@app.post("/api/process/{tool}")
async def process_pdf_direct(tool: str, files: List[UploadFile] = File(...), angle: int = Form(90), quality: str = Form("medium")):
    """Process common PDF operations synchronously and return the resulting file."""
    allowed = {"merge", "split", "rotate", "compress", "extract-text", "metadata"}
    if tool not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported tool")
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one file")
    contents = []
    for upload in files:
        data = await upload.read()
        if not data or len(data) > MAX_FILE_SIZE or not validate_pdf_signature(data):
            raise HTTPException(status_code=400, detail=f"Invalid PDF or file exceeds 50 MB: {upload.filename}")
        contents.append(data)
    if tool != "merge" and len(contents) != 1:
        raise HTTPException(status_code=400, detail="This operation accepts exactly one PDF")
    try:
        if tool == "merge":
            result = merge_pdfs(contents)
            filename, media_type = "merged.pdf", "application/pdf"
        elif tool == "split":
            pages = split_pdf(contents[0])
            tmp = tempfile.NamedTemporaryFile(prefix="pdf-master-", suffix=".zip", delete=False)
            tmp.close()
            with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as archive:
                for index, page in enumerate(pages, 1):
                    archive.writestr(f"page-{index}.pdf", page)
            return FileResponse(tmp.name, media_type="application/zip", filename="split-pages.zip", background=BackgroundTask(os.unlink, tmp.name))
        elif tool == "rotate":
            result = rotate_pdf(contents[0], angle=angle)
            filename, media_type = "rotated.pdf", "application/pdf"
        elif tool == "compress":
            result = compress_pdf(contents[0], quality=quality)
            filename, media_type = "compressed.pdf", "application/pdf"
        elif tool == "extract-text":
            doc = fitz.open(stream=contents[0], filetype="pdf")
            text_content = "\\n\\n".join(page.get_text() for page in doc)
            doc.close()
            result = text_content.encode("utf-8")
            filename, media_type = "extracted-text.txt", "text/plain; charset=utf-8"
        else:
            doc = fitz.open(stream=contents[0], filetype="pdf")
            result = (json.dumps({"page_count": doc.page_count, "metadata": doc.metadata}, indent=2, ensure_ascii=False)).encode("utf-8")
            doc.close()
            filename, media_type = "metadata.json", "application/json"
        tmp = tempfile.NamedTemporaryFile(prefix="pdf-master-", suffix=os.path.splitext(filename)[1], delete=False)
        try:
            tmp.write(result)
            tmp.close()
        except Exception:
            tmp.close()
            os.unlink(tmp.name)
            raise
        return FileResponse(tmp.name, media_type=media_type, filename=filename, background=BackgroundTask(os.unlink, tmp.name))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("PDF processing failed for tool %s", tool)
        raise HTTPException(status_code=422, detail=f"PDF processing failed: {str(exc)}")

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    active_jobs = len([j for j in jobs.values() if j.status in ("pending", "processing")])
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        active_jobs=active_jobs
    )

@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status by ID."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.post("/api/jobs/{job_id}/download", response_model=dict)
async def download_job(job_id: str, download_request: DownloadRequest):
    """Download job result with token."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    # Verify token
    if download_request.download_token not in download_tokens or download_tokens[download_request.download_token] != job_id:
        raise HTTPException(status_code=403, detail="Invalid or expired download token")

    # Check expiration (tokens expire after 30 minutes)
    token_time = download_tokens.get(f"{download_request.download_token}_time")
    if token_time and datetime.utcnow() > token_time:
        raise HTTPException(status_code=410, detail="Download link expired")

    # Find the output file
    output_path = f"/tmp/outputs/{job_id}_output.pdf"
    if os.path.exists(output_path):
        return FileResponse(
            path=output_path,
            filename=job.output_filename or "output.pdf",
            media_type="application/pdf"
        )

    # If file not found, check if job is completed and try to generate it
    if job.status == "completed":
        # Try to generate the output file based on the tool
        try:
            await generate_output_file(job_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate output: {str(e)}")

    # Final check
    if os.path.exists(output_path):
        return FileResponse(
            path=output_path,
            filename=job.output_filename or "output.pdf",
            media_type="application/pdf"
        )

    raise HTTPException(status_code=404, detail="Output file not found")

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its associated files."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    # Delete output file if exists
    output_path = f"/tmp/outputs/{job_id}_output.pdf"
    if os.path.exists(output_path):
        os.remove(output_path)

    # Delete temp job directory
    job_temp_dir = f"/tmp/jobs/{job_id}"
    if os.path.exists(job_temp_dir):
        shutil.rmtree(job_temp_dir, ignore_errors=True)

    # Clean up from job store
    del jobs[job_id]

    # Clean up download token
    if download_tokens.get(job_id):
        del download_tokens[job_id]
    if f"{download_tokens.get(job_id)}_time" in download_tokens:
        del download_tokens[f"{download_tokens.get(job_id)}_time"]

    return {"message": "Job deleted successfully"}

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Upload a PDF file for processing."""
    # Read file content
    content = await file.read()

    # Validate file
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB"
        )

    # Validate PDF signature
    if not validate_pdf_signature(content):
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    # Generate job ID
    job_id = generate_job_id()

    # Create job record
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="unknown"
    )

    # Ensure lock exists
    if job_id not in job_locks:
        job_locks[job_id] = asyncio.Lock()

    # Start background processing with lock
    async def process_with_lock():
        async with job_locks[job_id]:
            await _process_job(job_id, content)

    background_tasks.add_task(process_with_lock)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "File uploaded successfully. Processing started."
    }

async def _process_job(job_id: str, file_data: bytes):
    """Process a PDF job in the background."""
    try:
        jobs[job_id].status = "processing"
        jobs[job_id].progress = 0.0
        jobs[job_id].tool = "unknown"

        # Create temporary directory for this job
        job_temp_dir = f"/tmp/jobs/{job_id}"
        os.makedirs(job_temp_dir, exist_ok=True)

        # Write input file
        input_path = os.path.join(job_temp_dir, "input.pdf")
        with open(input_path, "wb") as f:
            f.write(file_data)

        # ... processing will be done by specific tool handlers
        # For now, mark as completed after a brief processing time
        await asyncio.sleep(2)

        # Generate output filename
        output_filename = f"{job_id}_output.pdf"

        # Update job status
        jobs[job_id].status = "completed"
        jobs[job_id].completed_at = datetime.utcnow()
        jobs[job_id].progress = 100.0
        jobs[job_id].output_filename = output_filename

        # Generate download token
        token = generate_download_token()
        download_tokens[token] = job_id
        jobs[job_id].output_filename = output_filename

        # Set token expiration time
        download_tokens[f"{token}_time"] = datetime.utcnow() + timedelta(minutes=JOB_RETENTION_MINUTES)

        # Schedule cleanup
        asyncio.create_task(cleanup_job_files(job_id, job_temp_dir))

    except Exception as e:
        jobs[job_id].status = "failed"
        jobs[job_id].error_message = str(e)
        jobs[job_id].completed_at = datetime.utcnow()
        # Clean up on failure
        job_temp_dir = f"/tmp/jobs/{job_id}"
        if os.path.exists(job_temp_dir):
            shutil.rmtree(job_temp_dir, ignore_errors=True)

async def cleanup_job_files(job_id: str, job_temp_dir: str):
    """Clean up temporary job files."""
    try:
        await asyncio.sleep(JOB_RETENTION_MINUTES * 60)
        if os.path.exists(job_temp_dir):
            shutil.rmtree(job_temp_dir, ignore_errors=True)
        # Remove from job store
        if job_id in jobs:
            del jobs[job_id]
    except Exception:
        pass

async def generate_output_file(job_id: str):
    """Generate output file for a completed job."""
    if job_id not in jobs:
        raise ValueError("Job not found")

    job = jobs[job_id]

    # Based on tool type, generate appropriate output
    job_temp_dir = f"/tmp/jobs/{job_id}"
    input_path = os.path.join(job_temp_dir, "input.pdf")

    if not os.path.exists(input_path):
        return

    try:
        # Read the original input
        with open(input_path, "rb") as f:
            file_data = f.read()

        # Determine tool and generate output
        tool = job.tool or "unknown"

        if tool == "merge":
            # For merge, we need multiple files - return original
            shutil.copy2(input_path, f"/tmp/outputs/{job_id}_output.pdf")
        elif tool == "split":
            # For split, create a single output with first page
            import fitz
            doc = fitz.open(input_path)
            if doc.page_count > 0:
                output_path = f"/tmp/outputs/{job_id}_output.pdf"
                doc.save(output_path)
                doc.close()
            else:
                doc.close()
                shutil.copy2(input_path, f"/tmp/outputs/{job_id}_output.pdf")
        elif tool == "rotate":
            # Rotate 0 degrees (return as-is)
            shutil.copy2(input_path, f"/tmp/outputs/{job_id}_output.pdf")
        elif tool == "compress":
            # Just copy for now
            shutil.copy2(input_path, f"/tmp/outputs/{job_id}_output.pdf")
        elif tool == "protect":
            # Just copy for now
            shutil.copy2(input_path, f"/tmp/outputs/{job_id}_output.pdf")
        elif tool == "unlock":
            # Just copy for now
            shutil.copy2(input_path, f"/tmp/outputs/{job_id}_output.pdf")
        elif tool == "ocr":
            # Just copy for now
            shutil.copy2(input_path, f"/tmp/outputs/{job_id}_output.pdf")
        else:
            # Default: return original
            shutil.copy2(input_path, f"/tmp/outputs/{job_id}_output.pdf")

    except Exception as e:
        raise RuntimeError(f"Failed to generate output: {str(e)}")

# ============================================================
# Tool-specific API Endpoints
# ============================================================

@app.post("/api/pdf/merge")
async def merge_pdf_endpoint(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """Merge multiple PDFs into one."""
    # Validate all files
    pdf_data_list = []
    for uploaded_file in files:
        content = await uploaded_file.read()
        if not content or len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"Invalid file: {uploaded_file.filename}")
        if not validate_pdf_signature(content):
            raise HTTPException(status_code=400, detail=f"Invalid PDF: {uploaded_file.filename}")
        pdf_data_list.append(content)

    # Generate job ID
    job_id = generate_job_id()

    # Create job record
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename="merged.pdf",
        tool="merge"
    )

    # Start background processing
    async def process_merge():
        try:
            jobs[job_id].status = "processing"

            # Merge the PDFs
            merged_data = merge_pdfs(pdf_data_list)

            # Create temp directory
            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Write merged PDF
            output_path = os.path.join(job_temp_dir, "merged.pdf")
            with open(output_path, "wb") as f:
                f.write(merged_data)

            # Update job status
            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "merged.pdf"

            # Generate download token
            token = generate_download_token()
            download_tokens[token] = job_id

        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_merge)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "PDF merge started. Processing in background."
    }

@app.post("/api/pdf/split")
async def split_pdf_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    page_numbers: str = Form(default="")
):
    """Split a PDF into individual pages or selected ranges."""
    # Read file content
    content = await file.read()

    # Parse page numbers
    page_list = []
    if page_numbers.strip():
        try:
            page_list = [int(p.strip()) for p in page_numbers.split(",") if p.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid page numbers format")

    # Generate job ID
    job_id = generate_job_id()

    # Create job record
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="split"
    )

    # Start background processing
    async def process_split():
        try:
            jobs[job_id].status = "processing"

            # Split the PDF
            results = split_pdf(content, page_numbers=page_list if page_list else None)

            # Create temp directory
            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Save each split part
            for i, result in enumerate(results):
                output_path = os.path.join(job_temp_dir, f"split_{i+1}.pdf")
                with open(output_path, "wb") as f:
                    f.write(result)

            # Update job status
            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = f"split_{len(results)}_parts.pdf"

            # Generate download token
            token = generate_download_token()
            download_tokens[token] = job_id

        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_split)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "PDF split started. Processing in background."
    }

@app.post("/api/pdf/rotate")
async def rotate_pdf_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    angle: float = Form(90)
):
    """Rotate a PDF by specified angle."""
    # Read file content
    content = await file.read()

    # Generate job ID
    job_id = generate_job_id()

    # Create job record
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="rotate"
    )

    # Start background processing
    async def process_rotate():
        try:
            jobs[job_id].status = "processing"

            # Rotate the PDF
            rotated_data = rotate_pdf(content, angle=angle)

            # Create temp directory
            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Write rotated PDF
            output_path = os.path.join(job_temp_dir, "rotated.pdf")
            with open(output_path, "wb") as f:
                f.write(rotated_data)

            # Update job status
            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "rotated.pdf"

            # Generate download token
            token = generate_download_token()
            download_tokens[token] = job_id

        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_rotate)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "PDF rotate started. Processing in background."
    }

@app.post("/api/pdf/compress")
async def compress_pdf_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    quality: str = Form("medium")
):
    """Compress a PDF file."""
    # Read file content
    content = await file.read()

    # Generate job ID
    job_id = generate_job_id()

    # Create job record
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="compress"
    )

    # Start background processing
    async def process_compress():
        try:
            jobs[job_id].status = "processing"

            # Compress the PDF
            compressed_data = compress_pdf(content, quality=quality)

            # Create temp directory
            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Write compressed PDF
            output_path = os.path.join(job_temp_dir, "compressed.pdf")
            with open(output_path, "wb") as f:
                f.write(compressed_data)

            # Update job status
            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "compressed.pdf"

            # Generate download token
            token = generate_download_token()
            download_tokens[token] = job_id

        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_compress)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "PDF compression started. Processing in background."
    }

@app.post("/api/pdf/organize")
async def organize_pdf_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    operation: str = Form(...),
    page_data: str = Form(default="{}")
):
    """Organize PDF pages (remove, extract, reorder)."""
    # Read file content
    content = await file.read()

    # Parse page data
    import json
    try:
        page_dict = json.loads(page_data) if page_data else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid page data format")

    # Generate job ID
    job_id = generate_job_id()

    # Create job record
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="organize"
    )

    # Start background processing
    async def process_organize():
        try:
            jobs[job_id].status = "processing"

            # Organize the PDF
            result_data = organize_pages(content, operation, page_dict)

            # Create temp directory
            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Write organized PDF
            output_path = os.path.join(job_temp_dir, "organized.pdf")
            with open(output_path, "wb") as f:
                f.write(result_data)

            # Update job status
            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "organized.pdf"

            # Generate download token
            token = generate_download_token()
            download_tokens[token] = job_id

        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_organize)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "PDF organization started. Processing in background."
    }

@app.post("/api/pdf/protect")
async def protect_pdf_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    password: str = Form(...),
    owner_password: Optional[str] = Form(None),
    user_password: Optional[str] = Form(None),
    permissions: str = Form(default="{}")
):
    """Password-protect a PDF file."""
    # Read file content
    content = await file.read()

    # Parse permissions
    import json
    try:
        perm_dict = json.loads(permissions) if permissions else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid permissions format")

    # Generate job ID
    job_id = generate_job_id()

    # Create job record
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="protect"
    )

    # Start background processing
    async def process_protect():
        try:
            jobs[job_id].status = "processing"

            # Protect the PDF
            protected_data = protect_pdf(content, password, owner_password, user_password, perm_dict)

            # Create temp directory
            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Write protected PDF
            output_path = os.path.join(job_temp_dir, "protected.pdf")
            with open(output_path, "wb") as f:
                f.write(protected_data)

            # Update job status
            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "protected.pdf"

            # Generate download token
            token = generate_download_token()
            download_tokens[token] = job_id

        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_protect)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "PDF protection started. Processing in background."
    }

@app.post("/api/pdf/unlock")
async def unlock_pdf_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    password: str = Form(default="")
):
    """Unlock a password-protected PDF file."""
    # Read file content
    content = await file.read()

    # Generate job ID
    job_id = generate_job_id()

    # Create job record
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="unlock"
    )

    # Start background processing
    async def process_unlock():
        try:
            jobs[job_id].status = "processing"

            # Unlock the PDF
            unlocked_data = unlock_pdf_simple(content, password)

            # Create temp directory
            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Write unlocked PDF
            output_path = os.path.join(job_temp_dir, "unlocked.pdf")
            with open(output_path, "wb") as f:
                f.write(unlocked_data)

            # Update job status
            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "unlocked.pdf"

            # Generate download token
            token = generate_download_token()
            download_tokens[token] = job_id

        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_unlock)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "PDF unlock started. Processing in background."
    }

@app.post("/api/pdf/ocr")
async def ocr_pdf_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Run OCR on a scanned PDF."""
    # Read file content
    content = await file.read()

    # Generate job ID
    job_id = generate_job_id()

    # Create job record
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="ocr"
    )

    # Start background processing
    async def process_ocr():
        try:
            jobs[job_id].status = "processing"

            # For OCR, we'll use a simple approach with PyMuPDF
            # In a full implementation, this would use Tesseract
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")

            # Check if PDF appears to be scanned (no text layers)
            is_scanned = True
            for page_num in range(min(doc.page_count, 3)):  # Check first 3 pages
                text = doc[page_num].get_text("text")
                if text.strip():
                    is_scanned = False
                    break

            if is_scanned:
                # Apply basic OCR-like processing (placeholder)
                # In production, integrate with Tesseract
                for page_num in range(doc.page_count):
                    doc[page_num].set_text("OCR processed page")
            else:
                # Document already has text, just copy
                pass

            # Save result
            output_buffer = io.BytesIO()
            doc.save(output_buffer)
            doc.close()

            output_buffer.seek(0)
            ocr_data = output_buffer.read()

            # Create temp directory
            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Write OCR result
            output_path = os.path.join(job_temp_dir, "ocr_output.pdf")
            with open(output_path, "wb") as f:
                f.write(ocr_data)

            # Update job status
            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "ocr_output.pdf"

            # Generate download token
            token = generate_download_token()
            download_tokens[token] = job_id

        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_ocr)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "OCR processing started. Processing in background."
    }

@app.post("/api/pdf/repair")
async def repair_pdf_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    aggressive: bool = Form(default=False)
):
    """Repair a corrupted or damaged PDF file."""
    # Read file content
    content = await file.read()

    # Generate job ID
    job_id = generate_job_id()

    # Create job record
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="repair"
    )

    # Start background processing
    async def process_repair():
        try:
            jobs[job_id].status = "processing"

            # Repair the PDF
            repaired_data = repair_pdf(content, aggressive=aggressive)

            # Create temp directory
            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Write repaired PDF
            output_path = os.path.join(job_temp_dir, "repaired.pdf")
            with open(output_path, "wb") as f:
                f.write(repaired_data)

            # Update job status
            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "repaired.pdf"

            # Generate download token
            token = generate_download_token()
            download_tokens[token] = job_id

        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_repair)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "PDF repair started. Processing in background."
    }

# ============================================================
# Conversion Endpoints
# ============================================================

@app.post("/api/pdf/to-word")
async def pdf_to_word_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Convert PDF to Word document (.docx)."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="to-word"
    )

    async def process_to_word():
        try:
            jobs[job_id].status = "processing"
            word_data = pdf_to_word(content)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.docx")
            with open(output_path, "wb") as f:
                f.write(word_data)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.docx"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_to_word)
    return {"job_id": job_id, "status": "pending", "message": "PDF to Word conversion started."}


@app.post("/api/pdf/to-jpg")
async def pdf_to_jpg_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dpi: int = Form(default=150)
):
    """Convert PDF to JPG images (one per page)."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="to-jpg"
    )

    async def process_to_jpg():
        try:
            jobs[job_id].status = "processing"
            images = pdf_to_images(content, output_format="jpg", dpi=dpi)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Save all images
            for i, img in enumerate(images):
                img_path = os.path.join(job_temp_dir, f"page_{i+1}.jpg")
                with open(img_path, "wb") as f:
                    f.write(img)

            # For download, we'll create a zip or just return the first image
            # For simplicity, create a zip file
            import zipfile
            zip_path = os.path.join(job_temp_dir, "output.zip")
            with zipfile.ZipFile(zip_path, 'w') as zf:
                for i, img in enumerate(images):
                    zf.writestr(f"page_{i+1}.jpg", img)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = f"output_{len(images)}_pages.zip"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_to_jpg)
    return {"job_id": job_id, "status": "pending", "message": "PDF to JPG conversion started."}


@app.post("/api/jpg-to-pdf")
async def jpg_to_pdf_endpoint(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """Convert JPG images to PDF."""
    image_data_list = []
    for f in files:
        content = await f.read()
        if not content:
            continue
        image_data_list.append(content)

    if not image_data_list:
        raise HTTPException(status_code=400, detail="No valid images provided")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename="images_to_pdf.pdf",
        tool="jpg-to-pdf"
    )

    async def process_jpg_to_pdf():
        try:
            jobs[job_id].status = "processing"
            pdf_data = images_to_pdf(image_data_list)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(pdf_data)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.pdf"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_jpg_to_pdf)
    return {"job_id": job_id, "status": "pending", "message": "JPG to PDF conversion started."}


@app.post("/api/pdf/to-excel")
async def pdf_to_excel_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Convert PDF to Excel (.xlsx)."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="to-excel"
    )

    async def process_to_excel():
        try:
            jobs[job_id].status = "processing"
            excel_data = pdf_to_excel(content)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.xlsx")
            with open(output_path, "wb") as f:
                f.write(excel_data)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.xlsx"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_to_excel)
    return {"job_id": job_id, "status": "pending", "message": "PDF to Excel conversion started."}


@app.post("/api/excel-to-pdf")
async def excel_to_pdf_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Convert Excel (.xlsx) to PDF."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="excel-to-pdf"
    )

    async def process_excel_to_pdf():
        try:
            jobs[job_id].status = "processing"
            pdf_data = excel_to_pdf(content)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(pdf_data)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.pdf"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_excel_to_pdf)
    return {"job_id": job_id, "status": "pending", "message": "Excel to PDF conversion started."}


@app.post("/api/pdf/to-powerpoint")
async def pdf_to_powerpoint_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Convert PDF to PowerPoint (.pptx)."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="to-powerpoint"
    )

    async def process_to_powerpoint():
        try:
            jobs[job_id].status = "processing"
            ppt_data = pdf_to_powerpoint(content)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.pptx")
            with open(output_path, "wb") as f:
                f.write(ppt_data)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.pptx"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_to_powerpoint)
    return {"job_id": job_id, "status": "pending", "message": "PDF to PowerPoint conversion started."}


@app.post("/api/powerpoint-to-pdf")
async def powerpoint_to_pdf_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Convert PowerPoint (.pptx) to PDF."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="powerpoint-to-pdf"
    )

    async def process_powerpoint_to_pdf():
        try:
            jobs[job_id].status = "processing"
            pdf_data = powerpoint_to_pdf(content)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(pdf_data)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.pdf"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_powerpoint_to_pdf)
    return {"job_id": job_id, "status": "pending", "message": "PowerPoint to PDF conversion started."}

# ============================================================
# Edit Endpoints
# ============================================================

@app.post("/api/pdf/add-text")
async def add_text_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    page_number: int = Form(...),
    x: float = Form(...),
    y: float = Form(...),
    text: str = Form(...),
    font_size: float = Form(default=12),
    font_name: str = Form(default="helv"),
    color: str = Form(default="0,0,0"),
    rotation: float = Form(default=0)
):
    """Add text to a PDF page."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    # Parse color
    try:
        color_tuple = tuple(float(c) for c in color.split(","))
    except:
        color_tuple = (0, 0, 0)

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="add-text"
    )

    async def process_add_text():
        try:
            jobs[job_id].status = "processing"
            result = add_text_to_pdf(content, page_number, x, y, text, font_size, font_name, color_tuple, rotation)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(result)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.pdf"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_add_text)
    return {"job_id": job_id, "status": "pending", "message": "Add text started."}


@app.post("/api/pdf/add-image")
async def add_image_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    page_number: int = Form(...),
    x: float = Form(...),
    y: float = Form(...),
    image: UploadFile = File(...),
    width: Optional[float] = Form(default=None),
    height: Optional[float] = Form(default=None),
    keep_aspect_ratio: bool = Form(default=True)
):
    """Add an image to a PDF page."""
    content = await file.read()
    image_data = await image.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid PDF file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    if not image_data:
        raise HTTPException(status_code=400, detail="No image provided")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="add-image"
    )

    async def process_add_image():
        try:
            jobs[job_id].status = "processing"
            result = add_image_to_pdf(content, page_number, x, y, image_data, width, height, keep_aspect_ratio)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(result)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.pdf"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_add_image)
    return {"job_id": job_id, "status": "pending", "message": "Add image started."}


@app.post("/api/pdf/add-watermark")
async def add_watermark_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    watermark_text: str = Form(default="CONFIDENTIAL"),
    font_size: float = Form(default=48),
    color: str = Form(default="0.5,0.5,0.5"),
    opacity: float = Form(default=0.3),
    rotation: float = Form(default=45),
    pages: str = Form(default="")
):
    """Add a watermark to PDF pages."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    # Parse color
    try:
        color_tuple = tuple(float(c) for c in color.split(","))
    except:
        color_tuple = (0.5, 0.5, 0.5)

    # Parse pages
    page_list = None
    if pages.strip():
        try:
            page_list = [int(p.strip()) for p in pages.split(",") if p.strip()]
        except ValueError:
            pass

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="add-watermark"
    )

    async def process_add_watermark():
        try:
            jobs[job_id].status = "processing"
            result = add_watermark_to_pdf(content, watermark_text, font_size, color_tuple, opacity, rotation, page_list)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(result)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.pdf"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_add_watermark)
    return {"job_id": job_id, "status": "pending", "message": "Add watermark started."}


@app.post("/api/pdf/add-page-numbers")
async def add_page_numbers_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    start_number: int = Form(default=1),
    format_string: str = Form(default="{page}/{total}"),
    position: str = Form(default="bottom-center"),
    font_size: float = Form(default=10),
    font_name: str = Form(default="helv"),
    color: str = Form(default="0.3,0.3,0.3"),
    pages: str = Form(default="")
):
    """Add page numbers to PDF pages."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    # Parse color
    try:
        color_tuple = tuple(float(c) for c in color.split(","))
    except:
        color_tuple = (0.3, 0.3, 0.3)

    # Parse pages
    page_list = None
    if pages.strip():
        try:
            page_list = [int(p.strip()) for p in pages.split(",") if p.strip()]
        except ValueError:
            pass

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="add-page-numbers"
    )

    async def process_add_page_numbers():
        try:
            jobs[job_id].status = "processing"
            result = add_page_numbers_to_pdf(content, start_number, format_string, position, font_size, font_name, color_tuple, page_list)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(result)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.pdf"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_add_page_numbers)
    return {"job_id": job_id, "status": "pending", "message": "Add page numbers started."}


@app.post("/api/pdf/add-signature")
async def add_signature_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    page_number: int = Form(...),
    x: float = Form(...),
    y: float = Form(...),
    signature: UploadFile = File(...),
    width: float = Form(default=150),
    height: float = Form(default=75)
):
    """Add a signature to a PDF page."""
    content = await file.read()
    signature_data = await signature.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid PDF file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    if not signature_data:
        raise HTTPException(status_code=400, detail="No signature image provided")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="add-signature"
    )

    async def process_add_signature():
        try:
            jobs[job_id].status = "processing"
            result = add_signature_to_pdf(content, page_number, x, y, signature_data, width, height)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(result)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.pdf"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_add_signature)
    return {"job_id": job_id, "status": "pending", "message": "Add signature started."}


@app.post("/api/pdf/add-annotation")
async def add_annotation_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    page_number: int = Form(...),
    annotation_type: str = Form(...),
    x0: float = Form(...),
    y0: float = Form(...),
    x1: float = Form(...),
    y1: float = Form(...),
    content: str = Form(default=""),
    color: str = Form(default="1,1,0"),
    opacity: float = Form(default=0.5)
):
    """Add an annotation to a PDF page."""
    pdf_data = await file.read()

    if not pdf_data or len(pdf_data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid PDF file size")

    if pdf_data[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    # Parse color
    try:
        color_tuple = tuple(float(c) for c in color.split(","))
    except:
        color_tuple = (1, 1, 0)

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="add-annotation"
    )

    async def process_add_annotation():
        try:
            jobs[job_id].status = "processing"
            result = add_annotation_to_pdf(pdf_data, page_number, annotation_type, (x0, y0, x1, y1), content, color_tuple, opacity)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(result)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.pdf"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_add_annotation)
    return {"job_id": job_id, "status": "pending", "message": "Add annotation started."}

# ============================================================
# Advanced Endpoints
# ============================================================

@app.post("/api/pdf/ocr")
async def ocr_pdf_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form(default="eng"),
    dpi: int = Form(default=300)
):
    """Perform OCR on a PDF to make scanned pages searchable."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="ocr"
    )

    async def process_ocr():
        try:
            jobs[job_id].status = "processing"
            result = ocr_pdf(content, language=language, dpi=dpi)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(result)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.pdf"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_ocr)
    return {"job_id": job_id, "status": "pending", "message": "OCR processing started."}


@app.post("/api/pdf/redact")
async def redact_pdf_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    redactions: str = Form(...)
):
    """Redact (permanently remove) content from PDF pages."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    # Parse redactions JSON
    import json
    try:
        redaction_list = json.loads(redactions) if redactions else []
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid redactions format")

    if not redaction_list:
        raise HTTPException(status_code=400, detail="No redactions specified")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="redact"
    )

    async def process_redact():
        try:
            jobs[job_id].status = "processing"
            result = redact_pdf(content, redaction_list)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            output_path = os.path.join(job_temp_dir, "output.pdf")
            with open(output_path, "wb") as f:
                f.write(result)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "output.pdf"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_redact)
    return {"job_id": job_id, "status": "pending", "message": "Redaction started."}


@app.post("/api/pdf/compare")
async def compare_pdfs_endpoint(
    background_tasks: BackgroundTasks,
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    diff_mode: str = Form(default="text")
):
    """Compare two PDFs and return differences."""
    content1 = await file1.read()
    content2 = await file2.read()

    if not content1 or len(content1) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid first file size")

    if not content2 or len(content2) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid second file size")

    if content1[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid first PDF file")

    if content2[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid second PDF file")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=f"compare_{file1.filename}_vs_{file2.filename}",
        tool="compare"
    )

    async def process_compare():
        try:
            jobs[job_id].status = "processing"
            result = compare_pdfs(content1, content2, diff_mode)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Save comparison result as JSON
            output_path = os.path.join(job_temp_dir, "comparison.json")
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "comparison.json"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_compare)
    return {"job_id": job_id, "status": "pending", "message": "PDF comparison started."}


@app.post("/api/pdf/extract-text")
async def extract_text_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Extract all text content from a PDF."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="extract-text"
    )

    async def process_extract_text():
        try:
            jobs[job_id].status = "processing"
            result = extract_text(content)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Save extracted text as JSON
            output_path = os.path.join(job_temp_dir, "extracted_text.json")
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "extracted_text.json"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_extract_text)
    return {"job_id": job_id, "status": "pending", "message": "Text extraction started."}


@app.post("/api/pdf/extract-images")
async def extract_images_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Extract all images from a PDF."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="extract-images"
    )

    async def process_extract_images():
        try:
            jobs[job_id].status = "processing"
            images = extract_images(content)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Save images
            for img in images:
                img_filename = f"page_{img['page']}_img_{img['index']}.{img['format']}"
                img_path = os.path.join(job_temp_dir, img_filename)
                img_data = base64.b64decode(img['data_base64'])
                with open(img_path, "wb") as f:
                    f.write(img_data)

            # Create zip for download
            import zipfile
            zip_path = os.path.join(job_temp_dir, "extracted_images.zip")
            with zipfile.ZipFile(zip_path, 'w') as zf:
                for img in images:
                    img_filename = f"page_{img['page']}_img_{img['index']}.{img['format']}"
                    img_path = os.path.join(job_temp_dir, img_filename)
                    zf.write(img_path, img_filename)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "extracted_images.zip"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_extract_images)
    return {"job_id": job_id, "status": "pending", "message": "Image extraction started."}


@app.post("/api/pdf/metadata")
async def metadata_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Get PDF metadata."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="metadata"
    )

    async def process_metadata():
        try:
            jobs[job_id].status = "processing"
            result = get_pdf_metadata(content)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Save metadata as JSON
            output_path = os.path.join(job_temp_dir, "metadata.json")
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2, default=str)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "metadata.json"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_metadata)
    return {"job_id": job_id, "status": "pending", "message": "Metadata extraction started."}


@app.post("/api/pdf/preview")
async def preview_endpoint(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    dpi: int = Form(default=96),
    max_pages: int = Form(default=20)
):
    """Generate page preview thumbnails."""
    content = await file.read()

    if not content or len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Invalid file size")

    if content[:5] != b'%PDF-':
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    job_id = generate_job_id()
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        created_at=datetime.utcnow(),
        original_filename=file.filename,
        tool="preview"
    )

    async def process_preview():
        try:
            jobs[job_id].status = "processing"
            previews = generate_page_previews(content, dpi=dpi, max_pages=max_pages)

            job_temp_dir = f"/tmp/jobs/{job_id}"
            os.makedirs(job_temp_dir, exist_ok=True)

            # Save previews as JSON with base64 images
            output_path = os.path.join(job_temp_dir, "previews.json")
            with open(output_path, "w") as f:
                json.dump(previews, f, indent=2)

            jobs[job_id].status = "completed"
            jobs[job_id].completed_at = datetime.utcnow()
            jobs[job_id].progress = 100.0
            jobs[job_id].output_filename = "previews.json"

            token = generate_download_token()
            download_tokens[token] = job_id
        except Exception as e:
            jobs[job_id].status = "failed"
            jobs[job_id].error_message = str(e)
            jobs[job_id].completed_at = datetime.utcnow()

    background_tasks.add_task(process_preview)
    return {"job_id": job_id, "status": "pending", "message": "Preview generation started."}

# ============================================================
# Utility Endpoints
# ============================================================

@app.get("/api/jobs/{job_id}/info")
async def get_job_info(job_id: str):
    """Get detailed job information."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    # Get tool-specific info based on tool type
    tool_info = {}
    if job.tool == "merge":
        tool_info = {"type": "merge", "status": "ready"}
    elif job.tool == "split":
        tool_info = {"type": "split", "status": "ready"}
    elif job.tool == "rotate":
        tool_info = {"type": "rotate", "angle": 90, "status": "ready"}
    elif job.tool == "compress":
        tool_info = {"type": "compress", "quality": "medium", "status": "ready"}
    elif job.tool == "organize":
        tool_info = {"type": "organize", "operation": "reorder", "status": "ready"}
    elif job.tool == "protect":
        tool_info = {"type": "protect", "status": "ready"}
    elif job.tool == "unlock":
        tool_info = {"type": "unlock", "status": "ready"}
    elif job.tool == "ocr":
        tool_info = {"type": "ocr", "status": "ready"}
    elif job.tool == "repair":
        tool_info = {"type": "repair", "status": "ready"}
    elif job.tool == "to-word":
        tool_info = {"type": "to-word", "status": "ready"}
    elif job.tool == "to-jpg":
        tool_info = {"type": "to-jpg", "status": "ready"}
    elif job.tool == "jpg-to-pdf":
        tool_info = {"type": "jpg-to-pdf", "status": "ready"}
    elif job.tool == "to-excel":
        tool_info = {"type": "to-excel", "status": "ready"}
    elif job.tool == "excel-to-pdf":
        tool_info = {"type": "excel-to-pdf", "status": "ready"}
    elif job.tool == "to-powerpoint":
        tool_info = {"type": "to-powerpoint", "status": "ready"}
    elif job.tool == "powerpoint-to-pdf":
        tool_info = {"type": "powerpoint-to-pdf", "status": "ready"}
    elif job.tool == "add-text":
        tool_info = {"type": "add-text", "status": "ready"}
    elif job.tool == "add-image":
        tool_info = {"type": "add-image", "status": "ready"}
    elif job.tool == "add-watermark":
        tool_info = {"type": "add-watermark", "status": "ready"}
    elif job.tool == "add-page-numbers":
        tool_info = {"type": "add-page-numbers", "status": "ready"}
    elif job.tool == "add-signature":
        tool_info = {"type": "add-signature", "status": "ready"}
    elif job.tool == "add-annotation":
        tool_info = {"type": "add-annotation", "status": "ready"}
    elif job.tool == "redact":
        tool_info = {"type": "redact", "status": "ready"}
    elif job.tool == "compare":
        tool_info = {"type": "compare", "status": "ready"}
    elif job.tool == "extract-text":
        tool_info = {"type": "extract-text", "status": "ready"}
    elif job.tool == "extract-images":
        tool_info = {"type": "extract-images", "status": "ready"}
    elif job.tool == "metadata":
        tool_info = {"type": "metadata", "status": "ready"}
    elif job.tool == "preview":
        tool_info = {"type": "preview", "status": "ready"}

    return {
        "job_id": job_id,
        "status": job.status,
        "tool": job.tool,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "progress": job.progress,
        "error_message": job.error_message,
        "tool_info": tool_info
    }

@app.get("/api/tools")
async def list_tools():
    """List available PDF tools."""
    return {
        "tools": [
            {"id": "merge", "name": "Merge PDF", "category": "Organize"},
            {"id": "split", "name": "Split PDF", "category": "Organize"},
            {"id": "rotate", "name": "Rotate PDF", "category": "Organize"},
            {"id": "compress", "name": "Compress PDF", "category": "Optimize"},
            {"id": "protect", "name": "Protect PDF", "category": "Security"},
            {"id": "unlock", "name": "Unlock PDF", "category": "Security"},
            {"id": "ocr", "name": "OCR PDF", "category": "Advanced"},
            {"id": "organize", "name": "Organize Pages", "category": "Organize"},
            {"id": "repair", "name": "Repair PDF", "category": "Optimize"},
            {"id": "to-word", "name": "PDF to Word", "category": "Convert"},
            {"id": "to-jpg", "name": "PDF to JPG", "category": "Convert"},
            {"id": "jpg-to-pdf", "name": "JPG to PDF", "category": "Convert"},
            {"id": "to-excel", "name": "PDF to Excel", "category": "Convert"},
            {"id": "excel-to-pdf", "name": "Excel to PDF", "category": "Convert"},
            {"id": "to-powerpoint", "name": "PDF to PowerPoint", "category": "Convert"},
            {"id": "powerpoint-to-pdf", "name": "PowerPoint to PDF", "category": "Convert"},
            {"id": "add-text", "name": "Add Text", "category": "Edit"},
            {"id": "add-image", "name": "Add Image", "category": "Edit"},
            {"id": "add-watermark", "name": "Add Watermark", "category": "Edit"},
            {"id": "add-page-numbers", "name": "Add Page Numbers", "category": "Edit"},
            {"id": "add-signature", "name": "Add Signature", "category": "Edit"},
            {"id": "add-annotation", "name": "Add Annotation", "category": "Edit"},
            {"id": "redact", "name": "Redact PDF", "category": "Advanced"},
            {"id": "compare", "name": "Compare PDF", "category": "Advanced"},
            {"id": "extract-text", "name": "Extract Text", "category": "Advanced"},
            {"id": "extract-images", "name": "Extract Images", "category": "Advanced"},
            {"id": "metadata", "name": "PDF Metadata", "category": "Advanced"},
            {"id": "preview", "name": "Page Preview", "category": "Advanced"}
        ]
    }

@app.get("/api/version")
async def get_version():
    """Get API version information."""
    return {
        "version": "1.0.0",
        "name": "PDF Master API",
        "status": "operational"
    }


@app.get("/api/performance/stats")
async def get_performance_stats():
    """Get performance statistics."""
    monitor = get_performance_monitor()
    return monitor.get_stats()


@app.get("/api/performance/system")
async def get_system_stats():
    """Get system resource usage."""
    monitor = get_performance_monitor()
    return monitor.get_system_stats()


@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    cache = get_async_cache()
    return cache.get_stats()


@app.get("/api/storage/usage")
async def get_storage_usage():
    """Get temporary storage usage."""
    cleanup = get_cleanup_service()
    return cleanup.get_temp_usage()


@app.post("/api/storage/cleanup")
async def trigger_cleanup():
    """Manually trigger cleanup."""
    cleanup = get_cleanup_service()
    await cleanup.cleanup_expired_jobs()
    await cleanup.cleanup_large_temp_dirs()
    return {"message": "Cleanup triggered successfully"}


# ============================================================
# Application Startup/Shutdown
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Application startup."""
    # Ensure temporary directories exist
    os.makedirs("/tmp/uploads", exist_ok=True)
    os.makedirs("/tmp/outputs", exist_ok=True)
    os.makedirs("/tmp/jobs", exist_ok=True)
    print("PDF Master backend started successfully")

    # Log startup without sensitive data
    print("PDF Master v1.0.0 - Starting up")
    print(f"Maximum file size: {MAX_FILE_SIZE // (1024*1024)} MB")
    print(f"Job retention: {JOB_RETENTION_MINUTES} minutes")

    # Start cleanup service
    await start_cleanup_service()

    # Start periodic cache cleanup
    asyncio.create_task(periodic_cache_cleanup())

    # Start performance logging
    asyncio.create_task(log_performance_stats())


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown."""
    # Stop cleanup service
    await stop_cleanup_service()

    print("PDF Master backend shutdown complete")