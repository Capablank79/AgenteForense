"""
Errores específicos para el módulo hardware y vincular de discos.
"""

class HardwareError(Exception):
    """Excepción base para el módulo hardware."""
    pass

class PowerShellUnavailableError(HardwareError):
    """PowerShell no está disponible en la ruta especificada o falló la ejecución."""
    pass

class StorageModuleUnavailableError(HardwareError):
    """El módulo Storage de PowerShell no está disponible o falló."""
    pass

class DiskScanTimeoutError(HardwareError):
    """El escaneo de discos superó el tiempo límite configurado."""
    pass

class DiskScanParseError(HardwareError):
    """Falló el parseo del JSON devuelto por PowerShell."""
    pass

class DiskNotFoundError(HardwareError):
    """El disco físico especificado no existe o no fue encontrado."""
    pass

class DiskNotReadOnlyError(HardwareError):
    """El disco físico no tiene IsReadOnly=True."""
    pass

class SystemDiskBlockedError(HardwareError):
    """Intentó operar o vincular el disco de sistema (IsSystem=True)."""
    pass

class BootDiskBlockedError(HardwareError):
    """Intentó operar o vincular el disco de arranque (IsBoot=True)."""
    pass

class UnsupportedDiskRepresentationError(HardwareError):
    """Representación de disco no soportada (ej. LDM/dinámico no correlacionable)."""
    pass

class DiskIdentityConflictError(HardwareError):
    """Conflicto en la identidad reportada del disco."""
    pass

class MultipleCandidatesError(HardwareError):
    """Existen múltiples candidatos compatibles ambiguos."""
    pass

class DiskBindingNotConfirmedError(HardwareError):
    """El vínculo de disco no ha sido confirmado por un operador humano."""
    pass

class SourceChangedError(HardwareError):
    """El disco físico original cambió su estado, serial o atributos críticos en revalidación."""
    pass

class WriteBlockerNotFoundError(HardwareError):
    """El bloqueador de escritura especificado no existe."""
    pass

class UnresolvedRelationError(HardwareError):
    """La relación entre el bloqueador y el medio no está confirmada (CONFIRMED)."""
    pass

class WriteBlockerCrossAssignmentError(HardwareError):
    """Asignación cruzada no permitida entre bloqueadores y medios."""
    pass

