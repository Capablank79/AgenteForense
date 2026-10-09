"""
Excepciones específicas del módulo de adquisición E01.
"""

from agente_forense.core.errors import AgenteForenseError


class AcquisitionError(AgenteForenseError):
    """Excepción base para errores de adquisición E01."""
    pass


class EwfBinaryNotFoundError(AcquisitionError):
    """El binario ewfacquire.exe no existe en la ruta configurada."""
    pass


class EwfBinaryChangedError(AcquisitionError):
    """El hash SHA-256 de ewfacquire.exe no coincide con el valor verificado."""
    pass


class SourceChangedError(AcquisitionError):
    """El disco físico de origen sufrió cambios de estado o discrepancias antes de iniciar."""
    pass


class AdminPrivilegesRequiredError(AcquisitionError):
    """El proceso carece de privilegios suficientes para abrir el dispositivo físico."""
    pass


class DestinationInvalidError(AcquisitionError):
    """El directorio o volumen de destino no es válido o no existe."""
    pass


class SpaceBelowRawSizeError(AcquisitionError):
    """El espacio libre en destino es menor que el tamaño total del disco origen."""
    pass


class DestinationOnSourceDiskError(AcquisitionError):
    """El disco físico de destino coincide con el disco físico de origen."""
    pass


class TargetCollisionError(AcquisitionError):
    """Ya existen archivos o segmentos E01 con el target_basename en el destino."""
    pass


class IncompatibleFilesystemError(AcquisitionError):
    """El sistema de archivos de destino no soporta el tamaño de archivo esperado (ej. FAT32 > 4GB)."""
    pass


class HumanGateAbortedError(AcquisitionError):
    """La confirmación del Human Gate fue rechazada o no coincidió exactamente con 'ADQUIRIR'."""
    pass


class AcquisitionRunnerError(AcquisitionError):
    """Falla durante la ejecución del proceso runner de ewfacquire."""
    pass


class UnexpectedSegmentationError(AcquisitionError):
    """Se detectaron archivos de segmento adicionales inesperados (.E02, .E03, etc.)."""
    pass


class ProcessMissingError(AcquisitionError):
    """El proceso en segundo plano finalizó inesperadamente o no se encuentra activo durante recovery."""
    pass


class AcquisitionJobNotFoundError(AcquisitionError):
    """El Job de adquisición especificado no existe."""
    pass


class AcquisitionJobInvalidStateError(AcquisitionError):
    """El Job de adquisición se encuentra en un estado inválido para la operación solicitada."""
    pass


class AcquisitionProcessFailedError(AcquisitionError):
    """El proceso de adquisición falló o retornó un código de salida no cero."""
    pass


class SegmentedArtifactsError(AcquisitionError):
    """Se detectaron artefactos segmentados no permitidos."""
    pass


class AcquisitionIncompleteError(AcquisitionError):
    """La adquisición no se completó de forma íntegra."""
    pass
