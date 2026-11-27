"""
Cleanup Service for PDF Master
Handles automatic cleanup of temporary files and abandoned jobs.
"""

import os
import shutil
import asyncio
import time
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path


class CleanupService:
    """Manages cleanup of temporary files and job directories."""

    def __init__(
        self,
        base_temp_dir: Optional[str] = None,
        job_retention_minutes: int = 30,
        max_temp_size_mb: int = 1024,
        cleanup_interval_seconds: int = 300  # 5 minutes
    ):
        self.base_temp_dir = os.path.abspath(
            base_temp_dir
            or os.getenv("PDF_MASTER_TEMP_DIR", os.path.join(tempfile.gettempdir(), "pdf-master"))
        )
        self.job_retention_minutes = job_retention_minutes
        self.max_temp_size_mb = max_temp_size_mb
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None

        # Directory structure
        self.jobs_dir = os.path.join(self.base_temp_dir, "jobs")
        self.uploads_dir = os.path.join(self.base_temp_dir, "uploads")
        self.outputs_dir = os.path.join(self.base_temp_dir, "outputs")

    def start(self):
        """Start the background cleanup task."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._cleanup_loop())

    def stop(self):
        """Stop the background cleanup task."""
        self._running = False
        if self._task:
            self._task.cancel()

    async def _cleanup_loop(self):
        """Main cleanup loop that runs periodically."""
        while self._running:
            try:
                await self.cleanup_expired_jobs()
                await self.cleanup_large_temp_dirs()
            except Exception as e:
                print(f"Cleanup error: {e}")

            await asyncio.sleep(self.cleanup_interval_seconds)

    async def cleanup_expired_jobs(self):
        """Clean up expired job directories and files."""
        now = time.time()
        retention_seconds = self.job_retention_minutes * 60

        if not os.path.exists(self.jobs_dir):
            return

        for job_id in os.listdir(self.jobs_dir):
            job_path = os.path.join(self.jobs_dir, job_id)
            if not os.path.isdir(job_path):
                continue

            # Check directory age
            try:
                mtime = os.path.getmtime(job_path)
                if now - mtime > retention_seconds:
                    shutil.rmtree(job_path, ignore_errors=True)
                    print(f"Cleaned up expired job: {job_id}")
            except Exception:
                pass

        # Also check uploads and outputs directories
        for dir_path in [self.uploads_dir, self.outputs_dir]:
            if not os.path.exists(dir_path):
                continue

            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                if not os.path.isfile(file_path):
                    continue

                try:
                    mtime = os.path.getmtime(file_path)
                    if now - mtime > retention_seconds:
                        os.remove(file_path)
                        print(f"Cleaned up expired file: {filename}")
                except Exception:
                    pass

    async def cleanup_large_temp_dirs(self):
        """Clean up if temp directory exceeds size limit."""
        total_size = 0

        for dir_path in [self.jobs_dir, self.uploads_dir, self.outputs_dir]:
            if not os.path.exists(dir_path):
                continue

            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except Exception:
                        pass

        # If over limit, clean oldest files first
        max_size_bytes = self.max_temp_size_mb * 1024 * 1024
        if total_size > max_size_bytes:
            await self._cleanup_oldest_files(max_size_bytes)

    async def _cleanup_oldest_files(self, target_size_bytes: int):
        """Remove oldest files until under target size."""
        all_files = []

        for dir_path in [self.jobs_dir, self.uploads_dir, self.outputs_dir]:
            if not os.path.exists(dir_path):
                continue

            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        all_files.append((stat.st_mtime, file_path, stat.st_size))
                    except Exception:
                        pass

        # Sort by modification time (oldest first)
        all_files.sort(key=lambda x: x[0])

        current_size = sum(f[2] for f in all_files)

        for mtime, file_path, size in all_files:
            if current_size <= target_size_bytes:
                break

            try:
                os.remove(file_path)
                current_size -= size
                print(f"Removed large temp file: {file_path}")
            except Exception:
                pass

    def cleanup_job(self, job_id: str) -> bool:
        """Manually clean up a specific job's files."""
        job_path = os.path.join(self.jobs_dir, job_id)
        if os.path.exists(job_path):
            try:
                shutil.rmtree(job_path, ignore_errors=True)
                return True
            except Exception:
                return False
        return False

    def get_temp_usage(self) -> Dict:
        """Get current temporary storage usage."""
        usage = {
            "jobs_dir": 0,
            "uploads_dir": 0,
            "outputs_dir": 0,
            "total_mb": 0,
            "job_count": 0,
            "file_count": 0
        }

        for name, dir_path in [
            ("jobs_dir", self.jobs_dir),
            ("uploads_dir", self.uploads_dir),
            ("outputs_dir", self.outputs_dir)
        ]:
            if not os.path.exists(dir_path):
                continue

            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        usage[name] += size
                        usage["file_count"] += 1
                    except Exception:
                        pass

                usage["job_count"] += len(dirs)

        usage["total_mb"] = round(sum([
            usage["jobs_dir"],
            usage["uploads_dir"],
            usage["outputs_dir"]
        ]) / (1024 * 1024), 2)

        # Convert to MB
        for key in ["jobs_dir", "uploads_dir", "outputs_dir"]:
            usage[key] = round(usage[key] / (1024 * 1024), 2)

        return usage

    def ensure_directories(self):
        """Ensure all required directories exist."""
        for dir_path in [self.jobs_dir, self.uploads_dir, self.outputs_dir]:
            os.makedirs(dir_path, exist_ok=True)


# Global cleanup service instance
cleanup_service = CleanupService()


async def start_cleanup_service():
    """Start the cleanup service."""
    cleanup_service.ensure_directories()
    cleanup_service.start()


async def stop_cleanup_service():
    """Stop the cleanup service."""
    cleanup_service.stop()


def get_cleanup_service() -> CleanupService:
    """Get the cleanup service instance."""
    return cleanup_service