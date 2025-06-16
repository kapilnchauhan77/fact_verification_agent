"""
High-performance caching system for fact-checking operations
Implements Redis-like in-memory caching with TTL support
"""
import time
import threading
import hashlib
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with TTL support"""
    data: Any
    created_at: float
    ttl: float  # Time to live in seconds
    access_count: int = 0
    last_access: float = 0.0
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return (time.time() - self.created_at) > self.ttl
    
    def access(self) -> Any:
        """Access cache entry and update stats"""
        self.access_count += 1
        self.last_access = time.time()
        return self.data

class HighPerformanceCache:
    """Thread-safe high-performance cache with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600):
        """
        Initialize cache
        
        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired_cleanups': 0
        }
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                self._stats['misses'] += 1
                self._stats['expired_cleanups'] += 1
                return None
            
            self._stats['hits'] += 1
            return entry.access()
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            # Clean expired entries if cache is getting full
            if len(self._cache) >= self.max_size * 0.9:
                self._cleanup_expired()
            
            # If still full, evict LRU entries
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            
            entry = CacheEntry(
                data=value,
                created_at=time.time(),
                ttl=ttl
            )
            
            self._cache[key] = entry
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if (current_time - entry.created_at) > entry.ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]
            self._stats['expired_cleanups'] += 1
    
    def _evict_lru(self) -> None:
        """Evict least recently used entries"""
        if not self._cache:
            return
        
        # Sort by last access time (LRU first)
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_access if x[1].last_access > 0 else x[1].created_at
        )
        
        # Remove oldest 10% of entries
        evict_count = max(1, len(sorted_entries) // 10)
        for i in range(evict_count):
            key, _ = sorted_entries[i]
            del self._cache[key]
            self._stats['evictions'] += 1
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'expired_cleanups': 0
            }
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                **self._stats,
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': hit_rate,
                'fill_rate': len(self._cache) / self.max_size
            }
    
    def cache_decorator(self, ttl: Optional[float] = None):
        """Decorator for caching function results"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{func.__name__}:{self._generate_key(*args, **kwargs)}"
                
                # Try to get from cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result
                
                # Execute function and cache result
                logger.debug(f"Cache miss for {func.__name__}, executing...")
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator

# Global cache instances
search_cache = HighPerformanceCache(max_size=500, default_ttl=1800)  # 30 minutes
content_cache = HighPerformanceCache(max_size=1000, default_ttl=3600)  # 1 hour
source_cache = HighPerformanceCache(max_size=2000, default_ttl=7200)  # 2 hours

def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches"""
    return {
        'search_cache': search_cache.stats(),
        'content_cache': content_cache.stats(),
        'source_cache': source_cache.stats(),
        'total_memory_mb': (
            search_cache.stats()['size'] + 
            content_cache.stats()['size'] + 
            source_cache.stats()['size']
        ) * 0.001  # Rough estimation
    }

def clear_all_caches() -> None:
    """Clear all caches"""
    search_cache.clear()
    content_cache.clear()
    source_cache.clear()
    logger.info("All caches cleared")