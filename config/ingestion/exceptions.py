class IngestionError(Exception):
    """Base exception for candidate data ingestion errors."""


class UnsupportedFileTypeError(IngestionError):
    """Raised when the uploaded file type is unsupported."""


class FileReadError(IngestionError):
    """Raised when a CSV or Excel file cannot be read."""


class DataValidationError(IngestionError):
    """Raised when candidate data fails validation."""


class EmptyFileError(IngestionError):
    """Raised when the uploaded file contains no candidate records."""