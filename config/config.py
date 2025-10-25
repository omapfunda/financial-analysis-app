"""
Application configuration management
"""
import os
from datetime import timedelta


class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Cache settings
    CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 300))  # 5 minutes default
    CACHE_DIR = os.environ.get('CACHE_DIR', 'cache')
    
    # Portfolio settings
    MAX_PORTFOLIO_SIZE = int(os.environ.get('MAX_PORTFOLIO_SIZE', 50))
    MIN_PORTFOLIO_SIZE = int(os.environ.get('MIN_PORTFOLIO_SIZE', 1))
    
    # API settings
    API_TIMEOUT = int(os.environ.get('API_TIMEOUT', 30))  # 30 seconds
    MAX_RETRIES = int(os.environ.get('MAX_RETRIES', 3))
    
    # Data settings
    DATA_DIR = os.environ.get('DATA_DIR', 'data')
    PORTFOLIOS_DIR = os.path.join(DATA_DIR, 'portfolios')
    
    # Analysis settings
    DEFAULT_RISK_FREE_RATE = float(os.environ.get('DEFAULT_RISK_FREE_RATE', 0.02))  # 2%
    DEFAULT_MARKET_RETURN = float(os.environ.get('DEFAULT_MARKET_RETURN', 0.10))  # 10%
    
    # Valuation thresholds
    STRONG_BUY_THRESHOLD = float(os.environ.get('STRONG_BUY_THRESHOLD', 0.7))
    BUY_THRESHOLD = float(os.environ.get('BUY_THRESHOLD', 0.9))
    HOLD_THRESHOLD = float(os.environ.get('HOLD_THRESHOLD', 1.1))
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'
    
    # Shorter cache timeout for development
    CACHE_TIMEOUT = 60  # 1 minute


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Longer cache timeout for production
    CACHE_TIMEOUT = 900  # 15 minutes
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    
    # Disable caching for tests
    CACHE_TIMEOUT = 0
    
    # Test-specific settings
    WTF_CSRF_ENABLED = False


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])