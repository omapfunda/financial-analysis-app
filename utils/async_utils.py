"""
Utilities for asynchronous operations and performance improvements
"""
import asyncio
import aiohttp
import time
import random
from functools import wraps
from typing import List, Dict, Any, Optional, Callable
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry mechanism"""
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor


async def exponential_backoff_retry(func: Callable, *args, retry_config: RetryConfig = None, **kwargs):
    """
    Execute a function with exponential backoff retry mechanism
    """
    if retry_config is None:
        retry_config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(retry_config.max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt == retry_config.max_retries:
                logger.error(f"Function {func.__name__} failed after {retry_config.max_retries} retries: {e}")
                raise e
            
            # Calculate delay with jitter
            delay = min(
                retry_config.base_delay * (retry_config.backoff_factor ** attempt),
                retry_config.max_delay
            )
            jitter = random.uniform(0, 0.1) * delay
            total_delay = delay + jitter
            
            logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {total_delay:.2f}s")
            await asyncio.sleep(total_delay)
    
    raise last_exception


def async_timeout(timeout_seconds: float):
    """
    Decorator to add timeout to async functions
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
                raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
        return wrapper
    return decorator


async def fetch_stock_data_async(session: aiohttp.ClientSession, ticker: str, timeout: float = 30.0) -> Dict[str, Any]:
    """
    Asynchronously fetch stock data using yfinance in a thread pool
    """
    def _fetch_stock_sync(ticker: str) -> Dict[str, Any]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                'ticker': ticker,
                'info': info,
                'success': True,
                'error': None
            }
        except Exception as e:
            return {
                'ticker': ticker,
                'info': None,
                'success': False,
                'error': str(e)
            }
    
    # Run the synchronous yfinance call in a thread pool
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=1) as executor:
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(executor, _fetch_stock_sync, ticker),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            return {
                'ticker': ticker,
                'info': None,
                'success': False,
                'error': f'Timeout after {timeout} seconds'
            }


async def process_stocks_batch(tickers: List[str], batch_size: int = 10, timeout: float = 30.0) -> List[Dict[str, Any]]:
    """
    Process stocks in batches to avoid overwhelming the API
    """
    results = []
    
    # Create a single aiohttp session for all requests
    connector = aiohttp.TCPConnector(limit=batch_size, limit_per_host=batch_size)
    timeout_config = aiohttp.ClientTimeout(total=timeout)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout_config) as session:
        # Process tickers in batches
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} stocks")
            
            # Create tasks for the current batch
            tasks = [
                exponential_backoff_retry(
                    fetch_stock_data_async,
                    session,
                    ticker,
                    timeout=timeout,
                    retry_config=RetryConfig(max_retries=2, base_delay=0.5)
                )
                for ticker in batch
            ]
            
            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")
                    results.append({
                        'ticker': 'unknown',
                        'info': None,
                        'success': False,
                        'error': str(result)
                    })
                else:
                    results.append(result)
            
            # Small delay between batches to be respectful to APIs
            if i + batch_size < len(tickers):
                await asyncio.sleep(0.1)
    
    return results


def run_async_screener(tickers: List[str], batch_size: int = 10, timeout: float = 30.0) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for async stock processing
    """
    try:
        # Try to get the current event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an async context, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(process_stocks_batch(tickers, batch_size, timeout))
                )
                return future.result()
        except RuntimeError:
            # No event loop is running, we can use asyncio.run directly
            return asyncio.run(process_stocks_batch(tickers, batch_size, timeout))
    except Exception as e:
        logger.error(f"Error in async screener: {e}")
        # Fallback to synchronous processing
        return _fallback_sync_processing(tickers)


def _fallback_sync_processing(tickers: List[str]) -> List[Dict[str, Any]]:
    """
    Fallback synchronous processing if async fails
    """
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            results.append({
                'ticker': ticker,
                'info': info,
                'success': True,
                'error': None
            })
        except Exception as e:
            results.append({
                'ticker': ticker,
                'info': None,
                'success': False,
                'error': str(e)
            })
    return results


class AsyncCache:
    """
    Enhanced cache with async support and TTL
    """
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    async def get(self, key: str, ttl: int = 300) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self._cache:
            timestamp = self._timestamps.get(key, 0)
            if time.time() - timestamp < ttl:
                return self._cache[key]
            else:
                # Remove expired entry
                del self._cache[key]
                del self._timestamps[key]
        return None
    
    async def set(self, key: str, value: Any) -> None:
        """Set value in cache with timestamp"""
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        self._timestamps.clear()
    
    def size(self) -> int:
        """Get cache size"""
        return len(self._cache)


# Global async cache instance
async_cache = AsyncCache()