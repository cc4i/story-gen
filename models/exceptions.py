"""
Custom exceptions for the media generation application.
"""

class MediaGenerationError(Exception):
    """Base exception for all media generation errors."""
    pass

class APIError(MediaGenerationError):
    """Exception raised for API-related errors."""
    pass

class ValidationError(MediaGenerationError):
    """Exception raised for input validation errors."""
    pass

class FileUploadError(MediaGenerationError):
    """Exception raised for file upload errors."""
    pass

class GenerationError(MediaGenerationError):
    """Exception raised for media generation errors."""
    pass

class ConfigurationError(MediaGenerationError):
    """Exception raised for configuration errors."""
    pass

class StorageError(MediaGenerationError):
    """Exception raised for storage-related errors."""
    pass 