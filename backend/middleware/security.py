"""
Security Middleware for PDF Master
Handles rate limiting, request validation, and security headers.
"""

import time
import hashlib
from typing import Dict, Optional
from collections import defaultdict
from fastapi import Request, HTTPException, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using in-memory store."""

    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_counts: Dict[str, list] = defaultdict(list)
        self.hour_counts: Dict[str, list] = defaultdict(list)

    def get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try to get real IP from headers (for proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to client host
        if request.client:
            return request.client.host

        return "unknown"

    def is_rate_limited(self, client_id: str) -> tuple[bool, str]:
        """Check if client is rate limited. Returns (limited, period)."""
        now = time.time()

        # Clean old entries (older than 1 hour)
        minute_ago = now - 60
        hour_ago = now - 3600

        self.minute_counts[client_id] = [t for t in self.minute_counts[client_id] if t > minute_ago]
        self.hour_counts[client_id] = [t for t in self.hour_counts[client_id] if t > hour_ago]

        # Check minute limit
        if len(self.minute_counts[client_id]) >= self.requests_per_minute:
            return True, "minute"

        # Check hour limit
        if len(self.hour_counts[client_id]) >= self.requests_per_hour:
            return True, "hour"

        # Record this request
        self.minute_counts[client_id].append(now)
        self.hour_counts[client_id].append(now)

        return False, ""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if request.url.path in ["/health", "/api/version", "/api/tools"]:
            return await call_next(request)

        # Skip for OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)

        client_id = self.get_client_id(request)
        limited, period = self.is_rate_limited(client_id)

        if limited:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Too many requests per {period}.",
                    "retry_after": 60 if period == "minute" else 3600
                },
                headers={
                    "Retry-After": "60" if period == "minute" else "3600",
                    "X-RateLimit-Limit-Minute": str(self.requests_per_minute),
                    "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
                    "X-RateLimit-Remaining-Minute": str(max(0, self.requests_per_minute - len(self.minute_counts[client_id]))),
                    "X-RateLimit-Remaining-Hour": str(max(0, self.requests_per_hour - len(self.hour_counts[client_id])))
                }
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            max(0, self.requests_per_minute - len(self.minute_counts[client_id]))
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            max(0, self.requests_per_hour - len(self.hour_counts[client_id]))
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        return response


class FileValidationMiddleware(BaseHTTPMiddleware):
    """Validate uploaded files before processing."""

    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/bmp",
        "image/tiff",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

    def validate_file(self, content: bytes, filename: str) -> tuple[bool, str]:
        """Validate file content and metadata."""
        # Check file size
        if len(content) > self.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum allowed ({self.MAX_FILE_SIZE // (1024*1024)} MB)"

        if len(content) == 0:
            return False, "Empty file"

        # Check PDF signature for PDF files
        if filename.lower().endswith(".pdf"):
            if content[:5] != b'%PDF-':
                return False, "Invalid PDF file signature"

        # Check image signatures
        if filename.lower().endswith((".jpg", ".jpeg")):
            if content[:2] != b'\xFF\xD8':
                return False, "Invalid JPEG file signature"
        elif filename.lower().endswith(".png"):
            if content[:8] != b'\x89PNG\r\n\x1a\n':
                return False, "Invalid PNG file signature"
        elif filename.lower().endswith(".gif"):
            if content[:6] not in [b'GIF87a', b'GIF89a']:
                return False, "Invalid GIF file signature"

        return True, ""

    async def dispatch(self, request: Request, call_next):
        # Only validate file upload endpoints
        if request.method == "POST" and "/api/" in str(request.url):
            # Check content type for multipart/form-data
            content_type = request.headers.get("content-type", "")
            if "multipart/form-data" in content_type:
                # We can't easily validate without reading the body
                # This would be done in the endpoint itself
                pass

        return await call_next(request)


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    import secrets
    return secrets.token_urlsafe(length)


def hash_file_content(content: bytes) -> str:
    """Generate SHA-256 hash of file content for deduplication."""
    return hashlib.sha256(content).hexdigest()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log requests for audit and debugging."""

    def __init__(self, app, log_body: bool = False):
        super().__init__(app)
        self.log_body = log_body

    async def dispatch(self, request: Request, call_next):
        import logging
        import time

        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"

        # Log request
        logging.info(f"Request: {request.method} {request.url.path} from {client_ip}")

        try:
            response = await call_next(request)

            process_time = time.time() - start_time
            logging.info(
                f"Response: {response.status_code} for {request.method} {request.url.path} "
                f"({process_time:.3f}s)"
            )

            # Add timing header
            response.headers["X-Process-Time"] = f"{process_time:.3f}"

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logging.error(
                f"Error: {type(e).__name__} for {request.method} {request.url.path} "
                f"({process_time:.3f}s): {str(e)}"
            )
            raise