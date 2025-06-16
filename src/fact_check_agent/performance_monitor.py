"""
Performance Monitoring and Optimization for Fact Check Agent
"""
import time
import asyncio
import logging
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
from functools import wraps
import threading

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitors and optimizes system performance"""
    
    def __init__(self):
        """Initialize performance monitor"""
        self.metrics = defaultdict(list)
        self.cache = {}
        self.cache_max_size = 1000
        self.cache_ttl = 3600  # 1 hour
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.response_times = defaultdict(deque)
        self.concurrent_requests = 0
        self.max_concurrent = 10
        self._lock = threading.Lock()
    
    def timing_decorator(self, operation_name: str):
        """Decorator to measure operation timing"""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    success = True
                    error = None
                except Exception as e:
                    result = None
                    success = False
                    error = str(e)
                    raise
                finally:
                    end_time = time.time()
                    duration = end_time - start_time
                    self._record_metric(operation_name, duration, success, error)
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    success = True
                    error = None
                except Exception as e:
                    result = None
                    success = False
                    error = str(e)
                    raise
                finally:
                    end_time = time.time()
                    duration = end_time - start_time
                    self._record_metric(operation_name, duration, success, error)
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def _record_metric(self, operation: str, duration: float, success: bool, error: str = None):
        """Record performance metric"""
        with self._lock:
            timestamp = datetime.now().isoformat()
            metric = {
                'timestamp': timestamp,
                'duration': duration,
                'success': success,
                'error': error
            }
            
            self.metrics[operation].append(metric)
            self.response_times[operation].append(duration)
            
            # Keep only last 1000 metrics per operation
            if len(self.metrics[operation]) > 1000:
                self.metrics[operation] = self.metrics[operation][-1000:]
            
            # Keep only last 100 response times for calculating averages
            if len(self.response_times[operation]) > 100:
                self.response_times[operation].popleft()
            
            self.request_counts[operation] += 1
            if not success:
                self.error_counts[operation] += 1
    
    async def throttle_concurrent_requests(self):
        """Throttle concurrent requests to prevent overload"""
        while self.concurrent_requests >= self.max_concurrent:
            await asyncio.sleep(0.1)
        
        with self._lock:
            self.concurrent_requests += 1
    
    def release_concurrent_request(self):
        """Release a concurrent request slot"""
        with self._lock:
            if self.concurrent_requests > 0:
                self.concurrent_requests -= 1
    
    def get_cache_key(self, operation: str, *args, **kwargs) -> str:
        """Generate cache key for operation"""
        key_data = f"{operation}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if still valid"""
        if cache_key not in self.cache:
            return None
        
        cached_item = self.cache[cache_key]
        if time.time() - cached_item['timestamp'] > self.cache_ttl:
            # Cache expired
            del self.cache[cache_key]
            return None
        
        return cached_item['result']
    
    def cache_result(self, cache_key: str, result: Any):
        """Cache operation result"""
        # Implement LRU eviction if cache is full
        if len(self.cache) >= self.cache_max_size:
            # Remove oldest 10% of entries
            sorted_items = sorted(
                self.cache.items(),
                key=lambda x: x[1]['timestamp']
            )
            items_to_remove = int(self.cache_max_size * 0.1)
            for key, _ in sorted_items[:items_to_remove]:
                del self.cache[key]
        
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        with self._lock:
            metrics = {}
            
            for operation, times in self.response_times.items():
                if times:
                    avg_time = sum(times) / len(times)
                    min_time = min(times)
                    max_time = max(times)
                    total_requests = self.request_counts[operation]
                    error_count = self.error_counts[operation]
                    error_rate = (error_count / total_requests) * 100 if total_requests > 0 else 0
                    
                    metrics[operation] = {
                        'average_response_time': avg_time,
                        'min_response_time': min_time,
                        'max_response_time': max_time,
                        'total_requests': total_requests,
                        'error_count': error_count,
                        'error_rate_percent': error_rate,
                        'last_100_avg': avg_time
                    }
            
            # Overall system metrics
            metrics['system'] = {
                'concurrent_requests': self.concurrent_requests,
                'max_concurrent': self.max_concurrent,
                'cache_size': len(self.cache),
                'cache_max_size': self.cache_max_size,
                'cache_hit_rate': self._calculate_cache_hit_rate()
            }
            
            return metrics
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate (placeholder - would need actual hit/miss tracking)"""
        # This is a simplified calculation
        return 0.0  # Would need to implement proper hit/miss tracking
    
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get performance alerts for issues that need attention"""
        alerts = []
        
        for operation, times in self.response_times.items():
            if not times:
                continue
            
            avg_time = sum(times) / len(times)
            error_rate = (self.error_counts[operation] / self.request_counts[operation]) * 100
            
            # Check for slow operations
            if operation == 'document_processing' and avg_time > 5.0:
                alerts.append({
                    'type': 'slow_processing',
                    'operation': operation,
                    'current_avg': avg_time,
                    'threshold': 5.0,
                    'message': f'Document processing averaging {avg_time:.2f}s (threshold: 5.0s)'
                })
            
            elif operation == 'claim_extraction' and avg_time > 3.0:
                alerts.append({
                    'type': 'slow_extraction',
                    'operation': operation,
                    'current_avg': avg_time,
                    'threshold': 3.0,
                    'message': f'Claim extraction averaging {avg_time:.2f}s (threshold: 3.0s)'
                })
            
            elif operation == 'fact_verification' and avg_time > 10.0:
                alerts.append({
                    'type': 'slow_verification',
                    'operation': operation,
                    'current_avg': avg_time,
                    'threshold': 10.0,
                    'message': f'Fact verification averaging {avg_time:.2f}s (threshold: 10.0s)'
                })
            
            # Check for high error rates
            if error_rate > 5.0:
                alerts.append({
                    'type': 'high_error_rate',
                    'operation': operation,
                    'error_rate': error_rate,
                    'threshold': 5.0,
                    'message': f'High error rate for {operation}: {error_rate:.1f}% (threshold: 5.0%)'
                })
        
        # Check concurrent request limits
        if self.concurrent_requests >= self.max_concurrent * 0.8:
            alerts.append({
                'type': 'high_concurrency',
                'current': self.concurrent_requests,
                'max': self.max_concurrent,
                'message': f'High concurrent requests: {self.concurrent_requests}/{self.max_concurrent}'
            })
        
        return alerts
    
    def optimize_settings(self) -> Dict[str, Any]:
        """Suggest optimizations based on performance data"""
        recommendations = []
        
        # Analyze performance patterns
        metrics = self.get_performance_metrics()
        
        for operation, data in metrics.items():
            if operation == 'system':
                continue
                
            avg_time = data.get('average_response_time', 0)
            error_rate = data.get('error_rate_percent', 0)
            
            if avg_time > 5.0:
                recommendations.append({
                    'operation': operation,
                    'issue': 'slow_response',
                    'suggestion': 'Consider increasing cache TTL or implementing parallel processing',
                    'current_avg': avg_time
                })
            
            if error_rate > 5.0:
                recommendations.append({
                    'operation': operation,
                    'issue': 'high_errors',
                    'suggestion': 'Implement additional retry logic or fallback mechanisms',
                    'error_rate': error_rate
                })
        
        # Cache optimization
        cache_size = len(self.cache)
        if cache_size > self.cache_max_size * 0.9:
            recommendations.append({
                'operation': 'caching',
                'issue': 'cache_full',
                'suggestion': 'Consider increasing cache size or reducing TTL',
                'cache_utilization': cache_size / self.cache_max_size
            })
        
        return {
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Convenience decorators
def monitor_performance(operation_name: str):
    """Decorator to monitor performance of a function"""
    return performance_monitor.timing_decorator(operation_name)

async def with_throttling(coro):
    """Execute coroutine with throttling"""
    await performance_monitor.throttle_concurrent_requests()
    try:
        result = await coro
        return result
    finally:
        performance_monitor.release_concurrent_request()

def with_caching(operation_name: str, cache_key_args: bool = True):
    """Decorator to add caching to a function"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key_args:
                cache_key = performance_monitor.get_cache_key(operation_name, *args, **kwargs)
            else:
                cache_key = performance_monitor.get_cache_key(operation_name)
            
            # Check cache
            cached_result = performance_monitor.get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            performance_monitor.cache_result(cache_key, result)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if cache_key_args:
                cache_key = performance_monitor.get_cache_key(operation_name, *args, **kwargs)
            else:
                cache_key = performance_monitor.get_cache_key(operation_name)
            
            # Check cache
            cached_result = performance_monitor.get_cached_result(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            performance_monitor.cache_result(cache_key, result)
            
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator