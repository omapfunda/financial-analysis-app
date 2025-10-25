"""
Data conversion utilities
"""


def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value) if value is not None and value != '' else default
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Safely convert value to integer"""
    try:
        return int(value) if value is not None and value != '' else default
    except (ValueError, TypeError):
        return default


def safe_percentage(value, default=0.0):
    """Safely convert value to percentage (0-100 range)"""
    try:
        val = float(value) if value is not None and value != '' else default
        return max(0, min(100, val))  # Clamp between 0 and 100
    except (ValueError, TypeError):
        return default