"""
Enhanced caching system for external API requests
"""
import time
import hashlib
import json
import pickle
import requests
from functools import wraps
from typing import Any, Optional, Dict, Callable
import yfinance as yf
from cache_manager import app_cache
import logging

logger = logging.getLogger(__name__)


class APICache:
    """
    Enhanced cache specifically for external API requests
    """
    
    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self._request_cache = {}
        self._yfinance_cache = {}
        
    def _generate_request_key(self, url: str, params: Dict = None, headers: Dict = None) -> str:
        """Generate cache key for HTTP requests"""
        key_data = {
            'url': url,
            'params': params or {},
            'headers': headers or {}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _generate_yfinance_key(self, ticker: str, method: str, **kwargs) -> str:
        """Generate cache key for yfinance requests"""
        key_data = {
            'ticker': ticker,
            'method': method,
            'kwargs': kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return f"yf_{hashlib.md5(key_string.encode()).hexdigest()}"


def cached_request(ttl: int = 300, cache_key_prefix: str = "req"):
    """
    Decorator for caching HTTP requests
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key based on function arguments
            cache_key = f"{cache_key_prefix}_{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = app_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                app_cache.set(cache_key, result, ttl=ttl)
                logger.debug(f"Cached result for {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error in cached request {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator


def cached_yfinance(ttl: int = 600):  # 10 minutes default for yfinance
    """
    Decorator specifically for caching yfinance operations
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract ticker from arguments
            ticker = args[0] if args else kwargs.get('ticker', 'unknown')
            
            # Generate cache key
            cache_key = f"yf_{func.__name__}_{ticker}_{hash(str(args[1:]) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = app_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"YFinance cache hit for {ticker} - {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                app_cache.set(cache_key, result, ttl=ttl)
                logger.debug(f"Cached YFinance result for {ticker} - {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error in cached yfinance {func.__name__} for {ticker}: {e}")
                raise
        
        return wrapper
    return decorator


@cached_request(ttl=900, cache_key_prefix="macrotrends")  # 15 minutes for MacroTrends
def get_macrotrends_data(url: str, headers: Dict = None) -> requests.Response:
    """
    Cached wrapper for MacroTrends requests
    """
    try:
        headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"MacroTrends request failed for {url}: {e}")
        raise


@cached_yfinance(ttl=600)  # 10 minutes for stock info
def get_yfinance_info(ticker: str) -> Dict:
    """
    Cached wrapper for yfinance stock info
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info:
            raise ValueError(f"No info available for ticker {ticker}")
        return info
    except Exception as e:
        logger.error(f"YFinance info request failed for {ticker}: {e}")
        raise


@cached_yfinance(ttl=1800)  # 30 minutes for historical data
def get_yfinance_history(ticker: str, period: str = "1y", interval: str = "1d") -> Any:
    """
    Cached wrapper for yfinance historical data
    """
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period, interval=interval)
        if history.empty:
            raise ValueError(f"No historical data available for ticker {ticker}")
        return history
    except Exception as e:
        logger.error(f"YFinance history request failed for {ticker}: {e}")
        raise


@cached_yfinance(ttl=3600)  # 1 hour for financials
def get_yfinance_financials(ticker: str, statement_type: str = "income") -> Any:
    """
    Cached wrapper for yfinance financial statements
    """
    try:
        stock = yf.Ticker(ticker)
        
        if statement_type == "income":
            financials = stock.financials
        elif statement_type == "balance":
            financials = stock.balance_sheet
        elif statement_type == "cashflow":
            financials = stock.cashflow
        else:
            raise ValueError(f"Invalid statement type: {statement_type}")
        
        if financials.empty:
            raise ValueError(f"No {statement_type} data available for ticker {ticker}")
        
        return financials
    except Exception as e:
        logger.error(f"YFinance {statement_type} request failed for {ticker}: {e}")
        raise


class SmartCache:
    """
    Smart caching system that adapts TTL based on data type and volatility
    """
    
    # TTL configurations for different data types
    TTL_CONFIG = {
        'stock_info': 600,      # 10 minutes - relatively stable
        'stock_price': 60,      # 1 minute - very volatile
        'financials': 3600,     # 1 hour - stable quarterly data
        'market_data': 300,     # 5 minutes - moderately volatile
        'company_info': 86400,  # 24 hours - very stable
        'screener': 900,        # 15 minutes - moderately stable
        'eight_pillars': 1800,  # 30 minutes - calculated data
    }
    
    @classmethod
    def get_ttl(cls, data_type: str) -> int:
        """Get appropriate TTL for data type"""
        return cls.TTL_CONFIG.get(data_type, 300)  # Default 5 minutes
    
    @classmethod
    def cache_with_smart_ttl(cls, data_type: str):
        """Decorator that uses smart TTL based on data type"""
        ttl = cls.get_ttl(data_type)
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = f"{data_type}_{func.__name__}_{hash(str(args) + str(kwargs))}"
                
                # Try cache first
                cached_result = app_cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Smart cache hit for {data_type} - {func.__name__}")
                    return cached_result
                
                # Execute and cache
                try:
                    result = func(*args, **kwargs)
                    app_cache.set(cache_key, result, ttl=ttl)
                    logger.debug(f"Smart cached {data_type} - {func.__name__} (TTL: {ttl}s)")
                    return result
                except Exception as e:
                    logger.error(f"Error in smart cached {func.__name__}: {e}")
                    raise
            
            return wrapper
        return decorator


# Convenience decorators for common use cases
def cache_stock_info(func):
    """Cache stock info with appropriate TTL"""
    return SmartCache.cache_with_smart_ttl('stock_info')(func)

def cache_financials(func):
    """Cache financial data with appropriate TTL"""
    return SmartCache.cache_with_smart_ttl('financials')(func)

def cache_market_data(func):
    """Cache market data with appropriate TTL"""
    return SmartCache.cache_with_smart_ttl('market_data')(func)

def cache_screener_data(func):
    """Cache screener data with appropriate TTL"""
    return SmartCache.cache_with_smart_ttl('screener')(func)


# Global enhanced cache instance
enhanced_cache = APICache()


def clear_all_caches():
    """Clear all caches"""
    app_cache.clear()
    enhanced_cache._request_cache.clear()
    enhanced_cache._yfinance_cache.clear()
    logger.info("All caches cleared")


def get_cache_stats():
    """Get comprehensive cache statistics"""
    base_stats = app_cache.get_stats()
    size_info = app_cache.get_size_info()
    
    return {
        'base_cache': base_stats,
        'size_info': size_info,
        'enhanced_cache_requests': len(enhanced_cache._request_cache),
        'enhanced_cache_yfinance': len(enhanced_cache._yfinance_cache),
    }