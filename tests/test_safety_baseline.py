"""
Tests de seguridad y baseline de reconstrucción (Fail-Closed, Git exclusions, etc).
"""

import subprocess
import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def test_path_config_protection():
    """Test 5: La configuración central no trata casos/ como código o tests."""
    from agente_forense.config.paths import PathConfig

    config = PathConfig()

    assert config.case_data_root.name == "casos"
    assert config.case_data_root != config.repository_root
    assert not str(config.case_data_root).startswith(str(config.repository_root / "src"))


def test_no_forensic_artifacts_in_git():
    """Test 6: Comprobar mediante Git que no estén versionados archivos E01, RAW, DD, IMG."""
    repo_root = Path(__file__).resolve().parent.parent
    cmd = ["git", "ls-files"]
    res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)

    assert res.returncode == 0
    files = res.stdout.splitlines()

    forbidden_exts = (".e01", ".e02", ".ex01", ".raw", ".dd", ".img")
    for f in files:
        assert not f.lower().endswith(forbidden_exts), f"Artefacto forense versionado: {f}"


def test_casos_folder_git_ignored():
    """Test 7: Comprobar que ningún archivo bajo casos/ figure en git ls-files."""
    repo_root = Path(__file__).resolve().parent.parent
    cmd = ["git", "ls-files", "casos/"]
    res = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)

    assert res.returncode == 0
    tracked_casos = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    assert len(tracked_casos) == 0, f"Archivos en casos/ versionados en Git: {tracked_casos}"


def test_no_forensic_dependencies():
    """Test 8: Importar package base no requiere binarios forenses ni SDKs externos."""
    import agente_forense

    # Aseguramos que la importación no levanta dependencias externas pesadas
    assert "ewfacquire" not in sys.modules
    assert "ewfverify" not in sys.modules
    assert "ollama" not in sys.modules
    assert "pytesseract" not in sys.modules
