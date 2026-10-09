"""
Exceptions for Petition Processing Pipeline (Sprint R05.1).
"""

class PetitionError(Exception):
    """Base exception for petition pipeline errors."""
    pass


class UnsupportedPetitionFormatError(PetitionError):
    """Raised when uploaded petition format is not supported."""
    pass


class PetitionIntegrityError(PetitionError):
    """Raised when document integrity (SHA-256) check fails."""
    pass


class PdfTextExtractionError(PetitionError):
    """Raised when pypdf fails to extract text from a text PDF."""
    pass


class PdfRenderError(PetitionError):
    """Raised when Windows.Data.Pdf fails to render PDF pages."""
    pass


class OcrUnavailableError(PetitionError):
    """Raised when Windows OCR runtime is not available."""
    pass


class OcrLanguageUnavailableError(PetitionError):
    """Raised when requested OCR language (e.g. es-ES) is not installed."""
    pass


class OcrProcessingError(PetitionError):
    """Raised when OCR processing fails."""
    pass


class PetitionExtractionConflictError(PetitionError):
    """Raised when material extraction conflicts block downstream operation."""
    pass


class PetitionNotReadyForDraftError(PetitionError):
    """Raised when draft generation is attempted before human review is completed."""
    pass
