"""
Entrypoint mínimo de Agente Forense.
"""

import sys
from agente_forense.core.states import SystemState


def main() -> int:
    state = SystemState.READY
    print("========================================")
    print("AGENTE FORENSE LOCAL - BASELINE")
    print(f"Estado del Sistema: {state.value}")
    print("Baseline de reconstrucción inicializado.")
    print("No se ejecutará ninguna operación forense.")
    print("========================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
