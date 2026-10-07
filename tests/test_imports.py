"""
Tests de importación y verificación base de la suite de reconstrucción.
"""

import sys
from pathlib import Path

# Asegurar que src esté en el sys.path para los tests
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def test_import_agente_forense():
    """Test 1: Import principal de agente_forense."""
    import agente_forense

    assert hasattr(agente_forense, "__version__")
    assert agente_forense.__version__ == "0.1.0"


def test_entrypoint_execution(capsys):
    """Test 2: Entrypoint mínimo no forense."""
    from agente_forense.__main__ import main

    exit_code = main()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "AGENTE FORENSE LOCAL - BASELINE" in captured.out
    assert "No se ejecutará ninguna operación forense." in captured.out


def test_states_base():
    """Test 3: Estados base mínimos son deterministas."""
    from agente_forense.core.states import SystemState

    assert SystemState.INITIALIZING.value == "INITIALIZING"
    assert SystemState.READY.value == "READY"
    assert SystemState.FAILED.value == "FAILED"
    assert SystemState.ABORTED.value == "ABORTED"


def test_errors_base():
    """Test 4: Excepciones base heredan correctamente de AgenteForenseError."""
    from agente_forense.core.errors import (
        AgenteForenseError,
        ConfigurationError,
        SafetyViolationError,
    )

    err = ConfigurationError("Error de prueba")
    safety_err = SafetyViolationError("Error de seguridad")

    assert isinstance(err, AgenteForenseError)
    assert isinstance(safety_err, AgenteForenseError)
