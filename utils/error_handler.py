"""
Centralized Error Handling and Logging System
Provides consistent error handling, logging, and response formatting across the application
"""
import logging
import traceback
from functools import wraps
from datetime import datetime
import os


class AppLogger:
    """Centralized logging configuration"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize logging for Flask app"""
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(app.root_path, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging
        log_level = app.config.get('LOG_LEVEL', 'INFO')
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'app.log'),
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Error file handler for errors only
        error_handler = logging.FileHandler(
            os.path.join(log_dir, 'errors.log'),
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(log_format))
        
        # Configure app logger
        app.logger.setLevel(getattr(logging, log_level))
        app.logger.addHandler(file_handler)
        app.logger.addHandler(error_handler)
        
        # Configure root logger for other modules
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)


class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def log_error(error, context=None):
        """Log error with context information"""
        logger = logging.getLogger(__name__)
        
        error_info = {
            'error': str(error),
            'type': type(error).__name__,
            'traceback': traceback.format_exc(),
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        
        # Add request context if available
        try:
            from flask import request
            if request:
                error_info['request'] = {
                    'method': request.method,
                    'url': request.url,
                    'remote_addr': request.remote_addr,
                    'user_agent': str(request.user_agent)
                }
        except (RuntimeError, ImportError):
            # Outside request context or Flask not available
            pass
        
        logger.error(f"Application Error: {error_info}")
        return error_info
    
    @staticmethod
    def handle_api_error(error, context=None):
        """Handle API errors and return JSON response"""
        from flask import jsonify
        
        error_info = ErrorHandler.log_error(error, context)
        
        # Determine error type and status code
        if isinstance(error, ValueError):
            status_code = 400
            error_type = "validation_error"
        elif isinstance(error, FileNotFoundError):
            status_code = 404
            error_type = "not_found"
        elif isinstance(error, PermissionError):
            status_code = 403
            error_type = "permission_denied"
        else:
            status_code = 500
            error_type = "internal_error"
        
        return jsonify({
            'success': False,
            'error': {
                'type': error_type,
                'message': str(error),
                'timestamp': error_info['timestamp']
            }
        }), status_code
    
    @staticmethod
    def handle_web_error(error, context=None, redirect_url=None):
        """Handle web errors and flash message"""
        from flask import flash, redirect, url_for
        
        ErrorHandler.log_error(error, context)
        
        # Flash error message
        flash(f'An error occurred: {str(error)}', 'error')
        
        # Redirect to appropriate page
        if redirect_url:
            return redirect(redirect_url)
        else:
            return redirect(url_for('main.dashboard'))


def handle_errors(error_type='web', redirect_url=None, context=None):
    """Decorator for automatic error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_context = context or {'function': func.__name__}
                
                if error_type == 'api':
                    return ErrorHandler.handle_api_error(e, error_context)
                else:
                    return ErrorHandler.handle_web_error(e, error_context, redirect_url)
        
        return wrapper
    return decorator


def log_function_call(func):
    """Decorator to log function calls for debugging"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(__name__)
        logger.debug(f"Calling {func.__name__} with args: {args}, kwargs: {kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {str(e)}")
            raise
    
    return wrapper


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class BusinessLogicError(Exception):
    """Custom exception for business logic errors"""
    pass


class DataAccessError(Exception):
    """Custom exception for data access errors"""
    pass


class ExternalAPIError(Exception):
    """Custom exception for external API errors"""
    pass


# Global instances
error_handler = ErrorHandler()
app_logger = AppLogger()