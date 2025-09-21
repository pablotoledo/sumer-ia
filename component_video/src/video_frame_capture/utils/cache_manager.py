"""
Advanced cache management with LRU implementation and memory monitoring.
"""

import threading
import time
import hashlib
from typing import Any, Optional, Dict, Callable, Tuple, List
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, Signal, QTimer
import gc


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    value: Any
    size_bytes: int
    access_count: int
    last_accessed: datetime
    created_at: datetime
    key_hash: str

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_accessed is None:
            self.last_accessed = self.created_at


class LRUCache:
    """Thread-safe LRU cache with size and memory limits"""

    def __init__(
        self,
        max_size: int = 100,
        max_memory_mb: int = 500,
        cleanup_callback: Optional[Callable[[Any], None]] = None,
        ttl_seconds: Optional[int] = None
    ):
        self.max_size = max_size
        self.max_memory = max_memory_mb * 1024 * 1024  # Convert to bytes
        self.cleanup_callback = cleanup_callback
        self.ttl_seconds = ttl_seconds

        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._memory_usage = 0
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
        self._lock = threading.RLock()

        # Background cleanup for TTL
        if ttl_seconds:
            self._cleanup_timer = threading.Timer(ttl_seconds / 2, self._cleanup_expired)
            self._cleanup_timer.daemon = True
            self._cleanup_timer.start()

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self._lock:
            if key not in self._cache:
                self._miss_count += 1
                return None

            entry = self._cache[key]

            # Check TTL
            if self._is_expired(entry):
                self._remove_entry(key)
                self._miss_count += 1
                return None

            # Update access info
            entry.access_count += 1
            entry.last_accessed = datetime.now()

            # Move to end (most recent)
            self._cache.move_to_end(key)

            self._hit_count += 1
            return entry.value

    def put(self, key: str, value: Any, size_bytes: int) -> None:
        """Add item to cache"""
        with self._lock:
            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)

            # Ensure we have space
            self._make_space(size_bytes)

            # Create and add new entry
            entry = CacheEntry(
                value=value,
                size_bytes=size_bytes,
                access_count=1,
                last_accessed=datetime.now(),
                created_at=datetime.now(),
                key_hash=self._hash_key(key)
            )

            self._cache[key] = entry
            self._memory_usage += size_bytes

    def remove(self, key: str) -> bool:
        """Remove specific item from cache"""
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False

    def clear(self) -> None:
        """Clear all cached items"""
        with self._lock:
            if self.cleanup_callback:
                for entry in self._cache.values():
                    self.cleanup_callback(entry.value)

            self._cache.clear()
            self._memory_usage = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._hit_count + self._miss_count
            hit_rate = self._hit_count / total_requests if total_requests > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "memory_usage_mb": self._memory_usage / (1024 * 1024),
                "max_memory_mb": self.max_memory / (1024 * 1024),
                "memory_usage_percent": (self._memory_usage / self.max_memory) * 100,
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate": hit_rate,
                "eviction_count": self._eviction_count,
            }

    def get_detailed_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics"""
        with self._lock:
            stats = self.get_stats()

            if self._cache:
                access_counts = [entry.access_count for entry in self._cache.values()]
                sizes = [entry.size_bytes for entry in self._cache.values()]
                ages = [
                    (datetime.now() - entry.created_at).total_seconds()
                    for entry in self._cache.values()
                ]

                stats.update({
                    "avg_access_count": sum(access_counts) / len(access_counts),
                    "max_access_count": max(access_counts),
                    "avg_entry_size_bytes": sum(sizes) / len(sizes),
                    "max_entry_size_bytes": max(sizes),
                    "avg_age_seconds": sum(ages) / len(ages),
                    "oldest_entry_seconds": max(ages),
                })

            return stats

    def resize(self, max_size: int, max_memory_mb: int) -> None:
        """Resize cache limits"""
        with self._lock:
            self.max_size = max_size
            self.max_memory = max_memory_mb * 1024 * 1024

            # Trim cache if necessary
            self._enforce_limits()

    def _make_space(self, needed_bytes: int) -> None:
        """Make space for new entry"""
        # Remove expired entries first
        self._cleanup_expired()

        # Remove LRU entries until we have space
        while (
            len(self._cache) >= self.max_size or
            self._memory_usage + needed_bytes > self.max_memory
        ):
            if not self._cache:
                break

            # Remove oldest (least recently used)
            oldest_key = next(iter(self._cache))
            self._remove_entry(oldest_key)
            self._eviction_count += 1

    def _remove_entry(self, key: str) -> None:
        """Remove entry and call cleanup"""
        entry = self._cache.pop(key, None)
        if entry:
            self._memory_usage -= entry.size_bytes
            if self.cleanup_callback:
                self.cleanup_callback(entry.value)

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if entry is expired"""
        if not self.ttl_seconds:
            return False

        age = (datetime.now() - entry.created_at).total_seconds()
        return age > self.ttl_seconds

    def _cleanup_expired(self) -> None:
        """Remove expired entries"""
        if not self.ttl_seconds:
            return

        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]

            for key in expired_keys:
                self._remove_entry(key)

    def _enforce_limits(self) -> None:
        """Enforce size and memory limits"""
        while (
            len(self._cache) > self.max_size or
            self._memory_usage > self.max_memory
        ):
            if not self._cache:
                break

            oldest_key = next(iter(self._cache))
            self._remove_entry(oldest_key)
            self._eviction_count += 1

    def _hash_key(self, key: str) -> str:
        """Generate hash for key"""
        return hashlib.md5(key.encode()).hexdigest()


class AdvancedCacheManager(QObject):
    """Advanced cache manager with multiple cache levels and monitoring"""

    # Signals
    cacheStatsChanged = Signal(dict)
    memoryWarning = Signal(float)  # Memory usage percentage
    cacheEviction = Signal(str, int)  # Cache name, evicted count

    def __init__(
        self,
        frame_cache_size: int = 50,
        frame_cache_memory_mb: int = 300,
        thumbnail_cache_size: int = 200,
        thumbnail_cache_memory_mb: int = 100,
        metadata_cache_size: int = 1000,
        metadata_cache_memory_mb: int = 50,
    ):
        super().__init__()

        # Initialize caches
        self.frame_cache = LRUCache(
            max_size=frame_cache_size,
            max_memory_mb=frame_cache_memory_mb,
            cleanup_callback=self._cleanup_frame,
            ttl_seconds=3600  # 1 hour TTL for frames
        )

        self.thumbnail_cache = LRUCache(
            max_size=thumbnail_cache_size,
            max_memory_mb=thumbnail_cache_memory_mb,
            cleanup_callback=self._cleanup_thumbnail,
            ttl_seconds=7200  # 2 hours TTL for thumbnails
        )

        self.metadata_cache = LRUCache(
            max_size=metadata_cache_size,
            max_memory_mb=metadata_cache_memory_mb,
            cleanup_callback=None,  # Metadata doesn't need special cleanup
            ttl_seconds=1800  # 30 minutes TTL for metadata
        )

        # Statistics timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._emit_stats)
        self.stats_timer.setInterval(10000)  # Every 10 seconds
        self.stats_timer.start()

        # Memory monitoring
        self._last_memory_check = 0
        self._memory_warning_threshold = 0.85

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

    def cache_metadata(self, key: str, metadata: Dict[str, Any]) -> None:
        """Cache metadata"""
        # Estimate metadata size (rough calculation)
        import sys
        size_bytes = sys.getsizeof(metadata)
        self.metadata_cache.put(key, metadata, size_bytes)

    def get_cached_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached metadata"""
        return self.metadata_cache.get(key)

    def clear_all_caches(self) -> None:
        """Clear all caches"""
        self.frame_cache.clear()
        self.thumbnail_cache.clear()
        self.metadata_cache.clear()
        gc.collect()  # Force garbage collection

    def clear_frame_cache(self) -> None:
        """Clear only frame cache"""
        self.frame_cache.clear()
        gc.collect()

    def clear_thumbnail_cache(self) -> None:
        """Clear only thumbnail cache"""
        self.thumbnail_cache.clear()
        gc.collect()

    def clear_metadata_cache(self) -> None:
        """Clear only metadata cache"""
        self.metadata_cache.clear()

    def optimize_memory(self) -> None:
        """Perform memory optimization"""
        # Get current stats
        frame_stats = self.frame_cache.get_stats()
        thumb_stats = self.thumbnail_cache.get_stats()

        # Clear older entries if memory usage is high
        if frame_stats["memory_usage_percent"] > 80:
            # Reduce frame cache by 50%
            new_size = max(10, frame_stats["size"] // 2)
            self.frame_cache.resize(new_size, frame_stats["max_memory_mb"])

        if thumb_stats["memory_usage_percent"] > 80:
            # Reduce thumbnail cache by 30%
            new_size = max(20, int(thumb_stats["size"] * 0.7))
            self.thumbnail_cache.resize(new_size, thumb_stats["max_memory_mb"])

        gc.collect()

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return {
            "frame_cache": self.frame_cache.get_detailed_stats(),
            "thumbnail_cache": self.thumbnail_cache.get_detailed_stats(),
            "metadata_cache": self.metadata_cache.get_detailed_stats(),
            "total_memory_mb": (
                self.frame_cache._memory_usage +
                self.thumbnail_cache._memory_usage +
                self.metadata_cache._memory_usage
            ) / (1024 * 1024),
            "total_entries": (
                len(self.frame_cache._cache) +
                len(self.thumbnail_cache._cache) +
                len(self.metadata_cache._cache)
            ),
        }

    def _cleanup_frame(self, frame_data: Any) -> None:
        """Cleanup callback for frame data"""
        # Custom cleanup logic for frames if needed
        pass

    def _cleanup_thumbnail(self, thumbnail_data: Any) -> None:
        """Cleanup callback for thumbnail data"""
        # Custom cleanup logic for thumbnails if needed
        pass

    def _emit_stats(self) -> None:
        """Emit cache statistics"""
        stats = self.get_comprehensive_stats()
        self.cacheStatsChanged.emit(stats)

        # Check memory usage
        total_memory_percent = 0
        for cache_name, cache_stats in stats.items():
            if isinstance(cache_stats, dict) and "memory_usage_percent" in cache_stats:
                total_memory_percent = max(total_memory_percent, cache_stats["memory_usage_percent"])

        if total_memory_percent > self._memory_warning_threshold * 100:
            self.memoryWarning.emit(total_memory_percent)

    def set_cache_sizes(
        self,
        frame_size: Optional[int] = None,
        thumbnail_size: Optional[int] = None,
        metadata_size: Optional[int] = None
    ) -> None:
        """Update cache sizes"""
        if frame_size is not None:
            current_stats = self.frame_cache.get_stats()
            self.frame_cache.resize(frame_size, current_stats["max_memory_mb"])

        if thumbnail_size is not None:
            current_stats = self.thumbnail_cache.get_stats()
            self.thumbnail_cache.resize(thumbnail_size, current_stats["max_memory_mb"])

        if metadata_size is not None:
            current_stats = self.metadata_cache.get_stats()
            self.metadata_cache.resize(metadata_size, current_stats["max_memory_mb"])

    def set_memory_limits(
        self,
        frame_memory_mb: Optional[int] = None,
        thumbnail_memory_mb: Optional[int] = None,
        metadata_memory_mb: Optional[int] = None
    ) -> None:
        """Update memory limits"""
        if frame_memory_mb is not None:
            current_stats = self.frame_cache.get_stats()
            self.frame_cache.resize(current_stats["size"], frame_memory_mb)

        if thumbnail_memory_mb is not None:
            current_stats = self.thumbnail_cache.get_stats()
            self.thumbnail_cache.resize(current_stats["size"], thumbnail_memory_mb)

        if metadata_memory_mb is not None:
            current_stats = self.metadata_cache.get_stats()
            self.metadata_cache.resize(current_stats["size"], metadata_memory_mb)


class SmartCache:
    """Smart cache with predictive loading and adaptive sizing"""

    def __init__(self, base_cache: LRUCache):
        self.base_cache = base_cache
        self._access_patterns: Dict[str, List[float]] = {}
        self._prediction_window = 10  # Number of recent accesses to consider

    def get(self, key: str) -> Optional[Any]:
        """Get item and record access pattern"""
        self._record_access(key)
        return self.base_cache.get(key)

    def put(self, key: str, value: Any, size_bytes: int) -> None:
        """Put item in cache"""
        self.base_cache.put(key, value, size_bytes)

    def predict_next_access(self, current_key: str) -> List[str]:
        """Predict next likely accessed keys"""
        # Simple pattern-based prediction
        # In a real implementation, this could use more sophisticated ML
        pattern = self._access_patterns.get(current_key, [])
        if len(pattern) < 2:
            return []

        # Look for patterns in recent accesses
        # This is a simplified example
        return []

    def _record_access(self, key: str) -> None:
        """Record access time for pattern analysis"""
        now = time.time()
        if key not in self._access_patterns:
            self._access_patterns[key] = []

        pattern = self._access_patterns[key]
        pattern.append(now)

        # Keep only recent accesses
        if len(pattern) > self._prediction_window:
            pattern.pop(0)