"""
Excepciones del agente de identificación fotográfica.
"""

class IdentificationError(Exception):
    """Excepción base para el módulo de identificación."""
    pass

class PhotoIntegrityError(IdentificationError):
    """Lanzada cuando SHA256 difiere antes/después del análisis o renombrado."""
    pass

class UnsupportedFormatError(IdentificationError):
    """Lanzada si el formato de imagen no es JPG/JPEG/PNG."""
    pass

class InvalidEntityError(IdentificationError):
    """Lanzada si no se especifica una entidad (ESPECIE o DSM) válida."""
    pass

class QwenTimeoutError(IdentificationError):
    """Lanzada cuando Qwen sobrepasa el timeout configurado."""
    pass

class RenameCollisionError(IdentificationError):
    """Lanzada si una propuesta de renombrado causa colisión de archivos."""
    pass
