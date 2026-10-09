"""
Verificador de integridad del binario ewfacquire.exe y descubrimiento de capacidades.
"""

import os
import hashlib
import subprocess
from pathlib import Path
from agente_forense.acquisition.errors import EwfBinaryNotFoundError, EwfBinaryChangedError
from agente_forense.acquisition.models import EwfBinaryCapabilities

# Constantes oficiales del Sprint R08.1
EXPECTED_EWF_PATH = r"J:\AgenteForense\ewftools-x64\ewfacquire.exe"
EXPECTED_EWF_SHA256 = "3cae1f37ece0b88746dc17810198b0171f4ca00ecb9c328e756baab5682e6791"


class EwfBinaryVerifier:
    """Verifica la presencia, firma hash SHA-256 y ejecución del binario ewfacquire.exe."""

    def __init__(
        self,
        binary_path: str = EXPECTED_EWF_PATH,
        expected_sha256: str = EXPECTED_EWF_SHA256
    ):
        self.binary_path = binary_path
        self.expected_sha256 = expected_sha256.lower()

    def calculate_sha256(self) -> str:
        if not os.path.exists(self.binary_path):
            raise EwfBinaryNotFoundError(f"El binario ewfacquire no existe en: {self.binary_path}")
        
        hasher = hashlib.sha256()
        with open(self.binary_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest().lower()

    def verify(self) -> EwfBinaryCapabilities:
        """Verifica la existencia y el SHA-256 exacto. Bloquea si cambió."""
        if not os.path.exists(self.binary_path):
            raise EwfBinaryNotFoundError(f"Binario ewfacquire.exe no encontrado en {self.binary_path}")
        
        current_hash = self.calculate_sha256()
        if current_hash != self.expected_sha256:
            raise EwfBinaryChangedError(
                f"EWFACQUIRE_BINARY_CHANGED: El hash del binario ({current_hash}) "
                f"no coincide con el esperado ({self.expected_sha256})."
            )

        # Obtener versión si es posible mediante -V
        version_str = "ewfacquire 20230405"
        try:
            res = subprocess.run([self.binary_path, "-V"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout:
                lines = res.stdout.strip().splitlines()
                if lines:
                    version_str = lines[0].strip()
        except Exception:
            pass

        return EwfBinaryCapabilities(
            path=self.binary_path,
            exists=True,
            sha256=current_hash,
            version=version_str,
            verified=True,
            single_e01_feasible=True,
            default_format="encase6",
            default_compression="best",
            supported_digests=["md5", "sha256"]
        )
