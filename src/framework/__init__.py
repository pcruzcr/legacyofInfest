"""
Module: __init__
System: framework
Academic Unit: N/A
Description: Framework package initialization. Exports FrameworkUsageError.
"""

class FrameworkUsageError(Exception):
    """Raised when student/stage code misuses the framework API (e.g., missing TMX layer)."""
