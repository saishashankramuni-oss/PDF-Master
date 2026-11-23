"""
Performance Optimization Service for PDF Master
Handles caching, connection pooling, and performance monitoring.
"""

import asyncio
import time
import os
import psutil
from typing import Dict, Any, Optional, Callable
from functools import wraps
from collections import defaultdict
from datetime import datetime
import logging


class PerformanceMonitor:
    """Monitor and track performance metrics."""

    def __init__(self):
        self.request_times: Dict[str, list] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.active_requests: Dict[str, int] = defaultdict(int)
        self.start_time = time.time()

    def record_request(self, endpoint: str, duration: float, success: bool = True):
        """Record a request's performance."""
        self.request_times[endpoint].append({
            "duration": duration,
            "timestamp": time.time(),
            "success": success
        })

        # Keep only last 1000 requests per endpoint
        if len(self.request_times[endpoint]) > 1000:
            self.request_times[endpoint] = self.request_times[endpoint][-1000:]

        if not success:
            self.error_counts[endpoint] += 1

    def record_active(self, endpoint: str, delta: int):
        """Track active requests."""
        self.active_requests[endpoint] += delta
        if self.active_requests[endpoint] < 0:
            self.active_requests[endpoint] = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {
            "uptime_seconds": time.time() - self.start_time,
            "endpoints": {}
        }

        for endpoint, requests in self.request_times.items():
            if not requests:
                continue

            durations = [r["duration"] for r in requests]
            successful = sum(1 for r in requests if r["success"])

            stats["endpoints"][endpoint] = {
                "total_requests": len(requests),
                "successful_requests": successful,
                "error_rate": round((len(requests) - successful) / len(requests) * 100, 2),
                "avg_duration_ms": round(sum(durations) / len(durations) * 1000, 2),
                "min_duration_ms": round(min(durations) * 1000, 2),
                "max_duration_ms": round(max(durations) * 1000, 2),
                "active_requests": self.active_requests.get(endpoint, 0),
                "error_count": self.error_counts.get(endpoint, 0)
            }

        return stats

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system resource usage."""
        try:
            process = psutil.Process(os.getpid())
            memory = process.memory_info()
            cpu_percent = process.cpu_percent(interval=0.1)

            return {
                "memory_mb": round(memory.rss / (1024 * 1024), 2),
                "memory_vms_mb": round(memory.vms / (1024 * 1024), 2),
                "cpu_percent": cpu_percent,
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections())
            }
        except Exception as e:
            return {"error": str(e)}


class AsyncCache:
    """Simple async-compatible cache with TTL."""

    def __init__(self, default_ttl: int = 300):
        self.cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if time.time() < expiry:
                    return value
                else:
                    del self.cache[key]
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        async with self._lock:
            ttl = ttl or self.default_ttl
            self.cache[key] = (value, time.time() + ttl)

    async def delete(self, key: str):
        """Delete key from cache."""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]

    async def clear(self):
        """Clear all cache."""
        async with self._lock:
            self.cache.clear()

    async def cleanup_expired(self):
        """Remove expired entries."""
        async with self._lock:
            now = time.time()
            expired = [k for k, (_, exp) in self.cache.items() if now >= exp]
            for k in expired:
                del self.cache[k]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        now = time.time()
        valid = sum(1 for _, exp in self.cache.values() if now < exp)
        expired = len(self.cache) - valid

        return {
            "total_entries": len(self.cache),
            "valid_entries": valid,
            "expired_entries": expired,
            "hit_rate": "N/A"  # Would need hit/miss tracking
        }


def performance_monitor(endpoint_name: str = None):
    """Decorator to monitor endpoint performance."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            name = endpoint_name or func.__name__

            monitor.record_active(name, 1)
            start = time.time()
            success = True

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start
                monitor.record_request(name, duration, success)
                monitor.record_active(name, -1)

        return wrapper
    return decorator


# Global instances
performance_monitor_instance = PerformanceMonitor()
async_cache = AsyncCache()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the performance monitor instance."""
    return performance_monitor_instance


def get_async_cache() -> AsyncCache:
    """Get the async cache instance."""
    return async_cache


async def periodic_cache_cleanup():
    """Periodically clean expired cache entries."""
    while True:
        await asyncio.sleep(60)  # Every minute
        await async_cache.cleanup_expired()


async def log_performance_stats():
    """Log performance stats periodically."""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        stats = performance_monitor_instance.get_stats()
        system = performance_monitor_instance.get_system_stats()

        logging.info(f"Performance stats: {stats}")
        logging.info(f"System stats: {system}")