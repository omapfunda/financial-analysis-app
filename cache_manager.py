"""
Cache Manager for Financial Analysis Application

This module provides a simple in-memory caching system with TTL (Time To Live)
functionality to cache API responses and improve application performance.
"""

import time
import threading
from typing import Any, Optional, Dict, Tuple
import hashlib
import json
import pandas as pd
import pickle
from functools import wraps


class CacheManager:
    """
    Thread-safe in-memory cache with TTL support
    """
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default TTL
        """
        Initialize the cache manager
        
        Args:
            default_ttl: Default time to live in seconds
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expiry_time)
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
    
    def _generate_key(self, *args, **kwargs) -> str:
        """
        Generate a cache key from function arguments
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            str: Cache key
        """
        # Create a string representation of all arguments
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        
        # Convert to JSON string and hash it
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key in self._cache:
                value, expiry_time = self._cache[key]
                
                # Check if expired
                if time.time() > expiry_time:
                    del self._cache[key]
                    self._stats['evictions'] += 1
                    self._stats['misses'] += 1
                    return None
                
                self._stats['hits'] += 1
                return value
            
            self._stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        expiry_time = time.time() + ttl
        
        with self._lock:
            self._cache[key] = (value, expiry_time)
            self._stats['sets'] += 1
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._stats = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'evictions': 0
            }
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, (value, expiry_time) in self._cache.items():
                if current_time > expiry_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
                self._stats['evictions'] += 1
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'total_entries': len(self._cache),
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate_percent': round(hit_rate, 2),
                'sets': self._stats['sets'],
                'evictions': self._stats['evictions']
            }
    
    def get_size_info(self) -> Dict[str, Any]:
        """
        Get cache size information
        
        Returns:
            Dictionary with size information
        """
        with self._lock:
            total_size = 0
            for key, (value, expiry_time) in self._cache.items():
                try:
                    # Estimate size using pickle
                    total_size += len(pickle.dumps(value))
                except:
                    # Fallback estimation
                    total_size += 1024  # 1KB estimate
            
            return {
                'total_entries': len(self._cache),
                'estimated_size_bytes': total_size,
                'estimated_size_mb': round(total_size / (1024 * 1024), 2)
            }


def cached(ttl: int = 300, cache_instance: Optional[CacheManager] = None):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        cache_instance: Cache instance to use (creates new if None)
        
    Returns:
        Decorated function
    """
    if cache_instance is None:
        cache_instance = CacheManager(default_ttl=ttl)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}_{cache_instance._generate_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result, ttl)
            
            return result
        
        # Add cache management methods to the wrapper
        wrapper.cache_clear = lambda: cache_instance.clear()
        wrapper.cache_stats = lambda: cache_instance.get_stats()
        wrapper.cache_size = lambda: cache_instance.get_size_info()
        
        return wrapper
    
    return decorator


# Global cache instance for the application
app_cache = CacheManager(default_ttl=300)  # 5 minutes default


def get_cache_key_for_ticker(ticker: str, method: str, **kwargs) -> str:
    """
    Generate a standardized cache key for ticker-related data
    
    Args:
        ticker: Stock ticker symbol
        method: Method name (e.g., 'info', 'price_history', 'financials')
        **kwargs: Additional parameters
        
    Returns:
        Cache key string
    """
    key_data = {
        'ticker': ticker.upper(),
        'method': method,
        'params': kwargs
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_dataframe(df: pd.DataFrame, key: str, ttl: int = 300) -> None:
    """
    Cache a pandas DataFrame
    
    Args:
        df: DataFrame to cache
        key: Cache key
        ttl: Time to live in seconds
    """
    if not df.empty:
        app_cache.set(key, df, ttl)


def get_cached_dataframe(key: str) -> Optional[pd.DataFrame]:
    """
    Get a cached pandas DataFrame
    
    Args:
        key: Cache key
        
    Returns:
        Cached DataFrame or None
    """
    return app_cache.get(key)