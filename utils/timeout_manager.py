"""
Configurable timeout management for external requests
"""
import asyncio
import signal
import time
import threading
from functools import wraps
from typing import Callable, Any, Optional, Dict, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import yfinance as yf
from config import get_config
import logging

logger = logging.getLogger(__name__)


class TimeoutConfig:
    """Configuration for different types of timeouts"""
    
    def __init__(
        self,
        connect_timeout: float = 10.0,
        read_timeout: float = 30.0,
        total_timeout: float = 60.0,
        pool_timeout: float = 5.0
    ):
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.total_timeout = total_timeout
        self.pool_timeout = pool_timeout
    
    @property
    def requests_timeout(self) -> tuple:
        """Get timeout tuple for requests library"""
        return (self.connect_timeout, self.read_timeout)
    
    def __str__(self):
        return (f"TimeoutConfig(connect={self.connect_timeout}, "
                f"read={self.read_timeout}, total={self.total_timeout})")


# Default timeout configurations for different services
DEFAULT_TIMEOUTS = {
    'yfinance': TimeoutConfig(
        connect_timeout=15.0,
        read_timeout=45.0,
        total_timeout=90.0,
        pool_timeout=10.0
    ),
    'macrotrends': TimeoutConfig(
        connect_timeout=10.0,
        read_timeout=30.0,
        total_timeout=60.0,
        pool_timeout=5.0
    ),
    'general': TimeoutConfig(
        connect_timeout=10.0,
        read_timeout=30.0,
        total_timeout=45.0,
        pool_timeout=5.0
    ),
    'fast': TimeoutConfig(
        connect_timeout=5.0,
        read_timeout=15.0,
        total_timeout=20.0,
        pool_timeout=3.0
    ),
    'slow': TimeoutConfig(
        connect_timeout=20.0,
        read_timeout=120.0,
        total_timeout=180.0,
        pool_timeout=15.0
    )
}


class TimeoutError(Exception):
    """Custom timeout exception"""
    pass


def timeout_handler(timeout_duration: float):
    """
    Decorator to add timeout to any function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout_duration)
            
            if thread.is_alive():
                # Force thread termination (not ideal but necessary)
                logger.error(f"Function {func.__name__} timed out after {timeout_duration}s")
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_duration} seconds")
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        
        return wrapper
    return decorator


async def async_timeout_handler(timeout_duration: float):
    """
    Async decorator to add timeout to async functions
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_duration
                )
            except asyncio.TimeoutError:
                logger.error(f"Async function {func.__name__} timed out after {timeout_duration}s")
                raise TimeoutError(f"Async function {func.__name__} timed out after {timeout_duration} seconds")
        
        return wrapper
    return decorator


class ConfigurableSession:
    """
    HTTP session with configurable timeouts and retry logic
    """
    
    def __init__(self, timeout_config: TimeoutConfig, service_name: str = "general"):
        self.timeout_config = timeout_config
        self.service_name = service_name
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a configured requests session"""
        session = requests.Session()
        
        # Configure retry strategy with compatibility for different urllib3 versions
        try:
            # Try the new parameter name first (urllib3 >= 1.26.0)
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"],
                backoff_factor=1
            )
        except TypeError:
            # Fallback to old parameter name for older urllib3 versions
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["HEAD", "GET", "OPTIONS"],
                backoff_factor=1
            )
        
        # Configure adapter with timeouts
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
            pool_block=True
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """GET request with configured timeout"""
        kwargs.setdefault('timeout', self.timeout_config.requests_timeout)
        return self.session.get(url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """POST request with configured timeout"""
        kwargs.setdefault('timeout', self.timeout_config.requests_timeout)
        return self.session.post(url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        """PUT request with configured timeout"""
        kwargs.setdefault('timeout', self.timeout_config.requests_timeout)
        return self.session.put(url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        """DELETE request with configured timeout"""
        kwargs.setdefault('timeout', self.timeout_config.requests_timeout)
        return self.session.delete(url, **kwargs)
    
    def close(self):
        """Close the session"""
        self.session.close()


class TimeoutManager:
    """
    Central manager for all timeout configurations
    """
    
    def __init__(self):
        self._sessions: Dict[str, ConfigurableSession] = {}
        self._timeouts = DEFAULT_TIMEOUTS.copy()
        
        # Load timeouts from config if available
        try:
            config = get_config()
            if hasattr(config, 'API_TIMEOUT'):
                # Update default timeouts based on config
                api_timeout = config.API_TIMEOUT
                for service in self._timeouts:
                    if service != 'fast':  # Keep fast timeout as is
                        self._timeouts[service].read_timeout = min(
                            self._timeouts[service].read_timeout, 
                            api_timeout
                        )
                        self._timeouts[service].total_timeout = min(
                            self._timeouts[service].total_timeout,
                            api_timeout + 15
                        )
        except Exception as e:
            logger.warning(f"Could not load timeout config: {e}")
    
    def get_session(self, service_name: str = "general") -> ConfigurableSession:
        """Get or create a configured session for a service"""
        if service_name not in self._sessions:
            timeout_config = self._timeouts.get(service_name, self._timeouts['general'])
            self._sessions[service_name] = ConfigurableSession(timeout_config, service_name)
        
        return self._sessions[service_name]
    
    def get_timeout_config(self, service_name: str = "general") -> TimeoutConfig:
        """Get timeout configuration for a service"""
        return self._timeouts.get(service_name, self._timeouts['general'])
    
    def update_timeout_config(self, service_name: str, timeout_config: TimeoutConfig):
        """Update timeout configuration for a service"""
        self._timeouts[service_name] = timeout_config
        
        # Recreate session if it exists
        if service_name in self._sessions:
            self._sessions[service_name].close()
            del self._sessions[service_name]
    
    def close_all_sessions(self):
        """Close all active sessions"""
        for session in self._sessions.values():
            session.close()
        self._sessions.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get timeout manager statistics"""
        return {
            'active_sessions': list(self._sessions.keys()),
            'timeout_configs': {
                name: str(config) for name, config in self._timeouts.items()
            }
        }


# Global timeout manager instance
timeout_manager = TimeoutManager()


def with_timeout(service_name: str = "general", timeout_override: Optional[float] = None):
    """
    Decorator to apply service-specific timeouts to functions
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            timeout_config = timeout_manager.get_timeout_config(service_name)
            timeout_duration = timeout_override or timeout_config.total_timeout
            
            return timeout_handler(timeout_duration)(func)(*args, **kwargs)
        
        return wrapper
    return decorator


def with_async_timeout(service_name: str = "general", timeout_override: Optional[float] = None):
    """
    Async decorator to apply service-specific timeouts to async functions
    """
    def decorator(func: Callable) -> Callable:
        timeout_config = timeout_manager.get_timeout_config(service_name)
        timeout_duration = timeout_override or timeout_config.total_timeout
        
        return async_timeout_handler(timeout_duration)(func)
    
    return decorator


# Convenience decorators for specific services
def yfinance_timeout(func):
    """Apply YFinance-specific timeout to function"""
    return with_timeout('yfinance')(func)


def macrotrends_timeout(func):
    """Apply MacroTrends-specific timeout to function"""
    return with_timeout('macrotrends')(func)


def fast_timeout(func):
    """Apply fast timeout to function"""
    return with_timeout('fast')(func)


def slow_timeout(func):
    """Apply slow timeout to function"""
    return with_timeout('slow')(func)


# Async versions
def async_yfinance_timeout(func):
    """Apply YFinance-specific timeout to async function"""
    return with_async_timeout('yfinance')(func)


def async_macrotrends_timeout(func):
    """Apply MacroTrends-specific timeout to async function"""
    return with_async_timeout('macrotrends')(func)


def async_fast_timeout(func):
    """Apply fast timeout to async function"""
    return with_async_timeout('fast')(func)


def async_slow_timeout(func):
    """Apply slow timeout to async function"""
    return with_async_timeout('slow')(func)


class YFinanceTimeoutWrapper:
    """
    Wrapper for yfinance operations with proper timeout handling
    """
    
    def __init__(self, timeout_config: Optional[TimeoutConfig] = None):
        self.timeout_config = timeout_config or DEFAULT_TIMEOUTS['yfinance']
    
    @yfinance_timeout
    def get_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """Get ticker info with timeout"""
        stock = yf.Ticker(ticker)
        return stock.info
    
    @yfinance_timeout
    def get_ticker_history(self, ticker: str, period: str = "1y", interval: str = "1d"):
        """Get ticker history with timeout"""
        stock = yf.Ticker(ticker)
        return stock.history(period=period, interval=interval)
    
    @yfinance_timeout
    def get_ticker_financials(self, ticker: str, statement_type: str = "income"):
        """Get ticker financials with timeout"""
        stock = yf.Ticker(ticker)
        
        if statement_type == "income":
            return stock.financials
        elif statement_type == "balance":
            return stock.balance_sheet
        elif statement_type == "cashflow":
            return stock.cashflow
        else:
            raise ValueError(f"Invalid statement type: {statement_type}")


# Global YFinance wrapper instance
yfinance_wrapper = YFinanceTimeoutWrapper()


def cleanup_timeout_manager():
    """Cleanup function to close all sessions"""
    timeout_manager.close_all_sessions()


# Register cleanup function
import atexit
atexit.register(cleanup_timeout_manager)