"""
Memory management for video frame caching and optimization.
"""

import gc
import psutil
from typing import Any, Optional, Dict, Callable
from collections import OrderedDict
import threading
from PySide6.QtCore import QObject, Signal, QTimer


class MemoryMonitor(QObject):
    """Monitor system memory usage and emit warnings"""

    memoryWarning = Signal(float)  # Memory usage percentage
    memoryCritical = Signal(float)  # Critical memory usage
    memoryNormal = Signal(float)  # Normal memory usage

    def __init__(self, warning_threshold: float = 0.8, critical_threshold: float = 0.9):
        super().__init__()
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self._last_state = "normal"

        # Monitor timer
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_memory)
        self.monitor_timer.setInterval(5000)  # Check every 5 seconds

    def start_monitoring(self) -> None:
        """Start memory monitoring"""
        self.monitor_timer.start()

    def stop_monitoring(self) -> None:
        """Stop memory monitoring"""
        self.monitor_timer.stop()

    def _check_memory(self) -> None:
        """Check current memory usage"""
        try:
            memory_percent = psutil.virtual_memory().percent / 100.0

            if memory_percent >= self.critical_threshold and self._last_state != "critical":
                self._last_state = "critical"
                self.memoryCritical.emit(memory_percent)
            elif (
                memory_percent >= self.warning_threshold
                and memory_percent < self.critical_threshold
                and self._last_state != "warning"
            ):
                self._last_state = "warning"
                self.memoryWarning.emit(memory_percent)
            elif memory_percent < self.warning_threshold and self._last_state != "normal":
                self._last_state = "normal"
                self.memoryNormal.emit(memory_percent)

        except Exception:
            pass  # Ignore errors in memory monitoring

    def get_memory_info(self) -> Dict[str, float]:
        """Get detailed memory information"""
        try:
            memory = psutil.virtual_memory()
            return {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "used_gb": memory.used / (1024**3),
                "percent": memory.percent,
            }
        except Exception:
            return {"total_gb": 0, "available_gb": 0, "used_gb": 0, "percent": 0}


class LRUCache:
    """Thread-safe LRU cache for video frames with memory tracking"""

    def __init__(
        self,
        max_size: int = 100,
        max_memory_mb: int = 500,
        cleanup_callback: Optional[Callable] = None,
    ):
        self.max_size = max_size
        self.max_memory = max_memory_mb * 1024 * 1024  # Convert to bytes
        self.cache = OrderedDict()
        self.memory_usage = 0
        self.lock = threading.RLock()
        self.cleanup_callback = cleanup_callback
        self._hit_count = 0
        self._miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            if key in self.cache:
                value, size = self.cache.pop(key)
                self.cache[key] = (value, size)  # Move to end (most recent)
                self._hit_count += 1
                return value
            self._miss_count += 1
            return None

    def put(self, key: str, value: Any, size_bytes: int) -> None:
        """Add item to cache with size tracking"""
        with self.lock:
            # Remove existing item if present
            if key in self.cache:
                _, old_size = self.cache.pop(key)
                self.memory_usage -= old_size

            # Remove items if necessary
            while (
                len(self.cache) >= self.max_size
                or self.memory_usage + size_bytes > self.max_memory
            ):
                if not self.cache:
                    break
                oldest_key, (oldest_value, oldest_size) = self.cache.popitem(last=False)
                self.memory_usage -= oldest_size
                if self.cleanup_callback:
                    self.cleanup_callback(oldest_value)

            # Add new item
            self.cache[key] = (value, size_bytes)
            self.memory_usage += size_bytes

    def remove(self, key: str) -> bool:
        """Remove specific item from cache"""
        with self.lock:
            if key in self.cache:
                value, size = self.cache.pop(key)
                self.memory_usage -= size
                if self.cleanup_callback:
                    self.cleanup_callback(value)
                return True
            return False

    def clear(self) -> None:
        """Clear all cached items"""
        with self.lock:
            if self.cleanup_callback:
                for value, _ in self.cache.values():
                    self.cleanup_callback(value)
            self.cache.clear()
            self.memory_usage = 0

    def get_stats(self) -> dict:
        """Get cache statistics"""
        with self.lock:
            total_requests = self._hit_count + self._miss_count
            hit_rate = self._hit_count / total_requests if total_requests > 0 else 0
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "memory_usage_mb": self.memory_usage / (1024 * 1024),
                "max_memory_mb": self.max_memory / (1024 * 1024),
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": hit_rate,
            }

    def resize(self, max_size: int, max_memory_mb: int) -> None:
        """Resize cache limits"""
        with self.lock:
            self.max_size = max_size
            self.max_memory = max_memory_mb * 1024 * 1024

            # Trim cache if necessary
            while len(self.cache) > self.max_size or self.memory_usage > self.max_memory:
                if not self.cache:
                    break
                oldest_key, (oldest_value, oldest_size) = self.cache.popitem(last=False)
                self.memory_usage -= oldest_size
                if self.cleanup_callback:
                    self.cleanup_callback(oldest_value)


class MemoryManager(QObject):
    """Manages memory for video frame caching and processing"""

    memoryStatusChanged = Signal(dict)  # Memory status information
    cacheCleared = Signal()  # Cache was cleared

    def __init__(self, max_cache_size: int = 100, max_cache_memory_mb: int = 500):
        super().__init__()
        self.frame_cache = LRUCache(
            max_size=max_cache_size,
            max_memory_mb=max_cache_memory_mb,
            cleanup_callback=self._cleanup_frame,
        )
        self.thumbnail_cache = LRUCache(
            max_size=max_cache_size * 2,  # More thumbnails
            max_memory_mb=max_cache_memory_mb // 4,  # Less memory per thumbnail
            cleanup_callback=self._cleanup_thumbnail,
        )

        # Memory monitor
        self.memory_monitor = MemoryMonitor()
        self.memory_monitor.memoryWarning.connect(self._on_memory_warning)
        self.memory_monitor.memoryCritical.connect(self._on_memory_critical)
        self.memory_monitor.start_monitoring()

        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._emit_status)
        self.status_timer.setInterval(10000)  # Every 10 seconds
        self.status_timer.start()

    def cache_frame(self, key: str, frame_data: Any, size_bytes: int) -> None:
        """Cache a video frame"""
        self.frame_cache.put(key, frame_data, size_bytes)

    def get_cached_frame(self, key: str) -> Optional[Any]:
        """Get cached video frame"""
        return self.frame_cache.get(key)

    def cache_thumbnail(self, key: str, thumbnail_data: Any, size_bytes: int) -> None:
        """Cache a thumbnail"""
        self.thumbnail_cache.put(key, thumbnail_data, size_bytes)

    def get_cached_thumbnail(self, key: str) -> Optional[Any]:
        """Get cached thumbnail"""
        return self.thumbnail_cache.get(key)

    def clear_all_caches(self) -> None:
        """Clear all caches"""
        self.frame_cache.clear()
        self.thumbnail_cache.clear()
        gc.collect()  # Force garbage collection
        self.cacheCleared.emit()

    def clear_frame_cache(self) -> None:
        """Clear only frame cache"""
        self.frame_cache.clear()
        gc.collect()

    def clear_thumbnail_cache(self) -> None:
        """Clear only thumbnail cache"""
        self.thumbnail_cache.clear()
        gc.collect()

    def optimize_memory(self) -> None:
        """Perform memory optimization"""
        # Clear half of the cache
        frame_stats = self.frame_cache.get_stats()
        thumbnail_stats = self.thumbnail_cache.get_stats()

        if frame_stats["size"] > 10:
            # Clear older frames
            with self.frame_cache.lock:
                items_to_remove = list(self.frame_cache.cache.keys())[
                    : frame_stats["size"] // 2
                ]
                for key in items_to_remove:
                    self.frame_cache.remove(key)

        if thumbnail_stats["size"] > 20:
            # Clear older thumbnails
            with self.thumbnail_cache.lock:
                items_to_remove = list(self.thumbnail_cache.cache.keys())[
                    : thumbnail_stats["size"] // 2
                ]
                for key in items_to_remove:
                    self.thumbnail_cache.remove(key)

        gc.collect()

    def _cleanup_frame(self, frame_data: Any) -> None:
        """Cleanup callback for frame data"""
        # Custom cleanup logic if needed
        pass

    def _cleanup_thumbnail(self, thumbnail_data: Any) -> None:
        """Cleanup callback for thumbnail data"""
        # Custom cleanup logic if needed
        pass

    def _on_memory_warning(self, usage: float) -> None:
        """Handle memory warning"""
        self.optimize_memory()

    def _on_memory_critical(self, usage: float) -> None:
        """Handle critical memory usage"""
        self.clear_all_caches()

    def _emit_status(self) -> None:
        """Emit memory status information"""
        memory_info = self.memory_monitor.get_memory_info()
        frame_stats = self.frame_cache.get_stats()
        thumbnail_stats = self.thumbnail_cache.get_stats()

        status = {
            "system_memory": memory_info,
            "frame_cache": frame_stats,
            "thumbnail_cache": thumbnail_stats,
            "total_cache_memory_mb": frame_stats["memory_usage_mb"]
            + thumbnail_stats["memory_usage_mb"],
        }

        self.memoryStatusChanged.emit(status)

    def get_memory_status(self) -> dict:
        """Get current memory status"""
        memory_info = self.memory_monitor.get_memory_info()
        frame_stats = self.frame_cache.get_stats()
        thumbnail_stats = self.thumbnail_cache.get_stats()

        return {
            "system_memory": memory_info,
            "frame_cache": frame_stats,
            "thumbnail_cache": thumbnail_stats,
            "total_cache_memory_mb": frame_stats["memory_usage_mb"]
            + thumbnail_stats["memory_usage_mb"],
        }