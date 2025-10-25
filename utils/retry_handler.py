"""
Robust retry mechanism with exponential backoff for external requests
"""
import time
import random
import logging
import asyncio
from functools import wraps
from typing import Callable, Any, Optional, Tuple, Type, Union, List
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError
import yfinance as yf
from config import get_config

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        backoff_factor: float = 1.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.backoff_factor = backoff_factor


class RetryableError(Exception):
    """Base class for errors that should trigger a retry"""
    pass


class NonRetryableError(Exception):
    """Base class for errors that should NOT trigger a retry"""
    pass


# Default retry configurations for different services
DEFAULT_CONFIGS = {
    'yfinance': RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True
    ),
    'macrotrends': RetryConfig(
        max_retries=4,
        base_delay=2.0,
        max_delay=60.0,
        exponential_base=2.0,
        jitter=True
    ),
    'general': RetryConfig(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True
    )
}


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate delay for exponential backoff with jitter
    """
    # Exponential backoff: base_delay * (exponential_base ^ attempt)
    delay = config.base_delay * (config.exponential_base ** attempt) * config.backoff_factor
    
    # Apply maximum delay limit
    delay = min(delay, config.max_delay)
    
    # Add jitter to prevent thundering herd
    if config.jitter:
        jitter_range = delay * 0.1  # 10% jitter
        delay += random.uniform(-jitter_range, jitter_range)
    
    return max(0, delay)


def is_retryable_error(error: Exception, retryable_exceptions: Tuple[Type[Exception], ...]) -> bool:
    """
    Determine if an error should trigger a retry
    """
    # Check if it's explicitly non-retryable
    if isinstance(error, NonRetryableError):
        return False
    
    # Check if it's explicitly retryable
    if isinstance(error, RetryableError):
        return True
    
    # Check against provided retryable exceptions
    if isinstance(error, retryable_exceptions):
        return True
    
    # Special handling for HTTP errors
    if isinstance(error, HTTPError):
        # Retry on server errors (5xx) but not client errors (4xx)
        if hasattr(error, 'response') and error.response is not None:
            status_code = error.response.status_code
            return 500 <= status_code < 600
    
    return False


def exponential_backoff_retry(
    config: Optional[RetryConfig] = None,
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        RequestException, ConnectionError, Timeout, TimeoutError, OSError
    ),
    service_type: str = 'general'
):
    """
    Decorator for implementing exponential backoff retry logic
    """
    if config is None:
        config = DEFAULT_CONFIGS.get(service_type, DEFAULT_CONFIGS['general'])
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # Log successful retry if this wasn't the first attempt
                    if attempt > 0:
                        logger.info(
                            f"Function {func.__name__} succeeded on attempt {attempt + 1}"
                        )
                    
                    return result
                
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if not is_retryable_error(e, retryable_exceptions):
                        logger.error(
                            f"Non-retryable error in {func.__name__}: {e}"
                        )
                        raise
                    
                    # Don't retry if we've exhausted attempts
                    if attempt >= config.max_retries:
                        logger.error(
                            f"Max retries ({config.max_retries}) exceeded for {func.__name__}: {e}"
                        )
                        break
                    
                    # Calculate delay and wait
                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


async def async_exponential_backoff_retry(
    config: Optional[RetryConfig] = None,
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        RequestException, ConnectionError, Timeout, TimeoutError, OSError, asyncio.TimeoutError
    ),
    service_type: str = 'general'
):
    """
    Async decorator for implementing exponential backoff retry logic
    """
    if config is None:
        config = DEFAULT_CONFIGS.get(service_type, DEFAULT_CONFIGS['general'])
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    
                    # Log successful retry if this wasn't the first attempt
                    if attempt > 0:
                        logger.info(
                            f"Async function {func.__name__} succeeded on attempt {attempt + 1}"
                        )
                    
                    return result
                
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry
                    if not is_retryable_error(e, retryable_exceptions):
                        logger.error(
                            f"Non-retryable error in async {func.__name__}: {e}"
                        )
                        raise
                    
                    # Don't retry if we've exhausted attempts
                    if attempt >= config.max_retries:
                        logger.error(
                            f"Max retries ({config.max_retries}) exceeded for async {func.__name__}: {e}"
                        )
                        break
                    
                    # Calculate delay and wait
                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"Async attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


# Convenience decorators for specific services
def retry_yfinance(func):
    """Retry decorator specifically configured for YFinance requests"""
    return exponential_backoff_retry(
        config=DEFAULT_CONFIGS['yfinance'],
        service_type='yfinance'
    )(func)


def retry_macrotrends(func):
    """Retry decorator specifically configured for MacroTrends requests"""
    return exponential_backoff_retry(
        config=DEFAULT_CONFIGS['macrotrends'],
        service_type='macrotrends'
    )(func)


def retry_general(func):
    """General retry decorator for other external requests"""
    return exponential_backoff_retry(
        config=DEFAULT_CONFIGS['general'],
        service_type='general'
    )(func)


# Async versions
def async_retry_yfinance(func):
    """Async retry decorator specifically configured for YFinance requests"""
    return async_exponential_backoff_retry(
        config=DEFAULT_CONFIGS['yfinance'],
        service_type='yfinance'
    )(func)


def async_retry_macrotrends(func):
    """Async retry decorator specifically configured for MacroTrends requests"""
    return async_exponential_backoff_retry(
        config=DEFAULT_CONFIGS['macrotrends'],
        service_type='macrotrends'
    )(func)


def async_retry_general(func):
    """General async retry decorator for other external requests"""
    return async_exponential_backoff_retry(
        config=DEFAULT_CONFIGS['general'],
        service_type='general'
    )(func)


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                else:
                    raise NonRetryableError(
                        f"Circuit breaker is OPEN for {func.__name__}"
                    )
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


# Global circuit breakers for different services
yfinance_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=120.0,  # 2 minutes
    expected_exception=Exception
)

macrotrends_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=300.0,  # 5 minutes
    expected_exception=Exception
)


def get_retry_stats() -> dict:
    """Get statistics about retry operations"""
    return {
        'yfinance_circuit_breaker': {
            'state': yfinance_circuit_breaker.state,
            'failure_count': yfinance_circuit_breaker.failure_count,
            'last_failure_time': yfinance_circuit_breaker.last_failure_time
        },
        'macrotrends_circuit_breaker': {
            'state': macrotrends_circuit_breaker.state,
            'failure_count': macrotrends_circuit_breaker.failure_count,
            'last_failure_time': macrotrends_circuit_breaker.last_failure_time
        }
    }