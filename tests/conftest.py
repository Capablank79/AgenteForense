"""
Configuración global de Pytest.
Asegura que durante la ejecución de pruebas la base de datos sea siempre 'agente_forense_test'.
"""

import os

os.environ["AGENTE_FORENSE_DB_NAME"] = "agente_forense_test"
os.environ["ENVIRONMENT"] = "TEST"
