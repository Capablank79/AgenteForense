"""
Configuración central de rutas del sistema.
"""

from pathlib import Path
from typing import Optional


class PathConfig:
    """Configuración central de rutas verificado en entorno real."""

    def __init__(
        self,
        repository_root: Optional[Path] = None,
        case_data_root: Optional[Path] = None,
        ewf_tools_root: Optional[Path] = None,
        ollama_models_root: Optional[Path] = None,
    ):
        self.repository_root = (
            repository_root or Path(r"J:\AgenteForense\AgenteForense")
        ).resolve()
        self.case_data_root = (
            case_data_root or self.repository_root / "casos"
        ).resolve()
        self.ewf_tools_root = (
            ewf_tools_root or Path(r"J:\AgenteForense\ewftools-x64")
        ).resolve()
        self.ollama_models_root = (
            ollama_models_root or Path(r"J:\AgenteForense\OllamaModels")
        ).resolve()

    def validate_roots_exist(self) -> bool:
        """Verifica que las rutas base configuradas existan físicamente."""
        return (
            self.repository_root.exists()
            and self.case_data_root.exists()
            and self.ewf_tools_root.exists()
            and self.ollama_models_root.exists()
        )
