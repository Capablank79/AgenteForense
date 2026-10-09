# SPRINT_R00 — Reinicialización técnica controlada desde cero

## 1. Objetivo

Crear el baseline técnico real del proyecto AGENTE FORENSE después de la pérdida del código anterior.

Este Sprint NO reconstruye funcionalidades forenses históricas.

Su único objetivo es dejar una base mínima, comprobable y segura desde la cual iniciar la nueva arquitectura.

## 2. Condición de partida

```text
SOURCE_CODE_LOST = true
TEST_SUITE_LOST = true
REIMPLEMENTATION_MODE = FROM_SCRATCH
```

No asumir que existe implementación anterior.

Los sprints históricos son documentación de referencia, no baseline de código.

## 3. Documentos obligatorios

Antes de cualquier modificación:

1. leer `PROMPT_MAESTRO.md`;
2. leer `REGLA_PERMANENTE_PRE_SPRINT.md`;
3. leer `ROADMAP_RECONSTRUCCION_AGENTE_FORENSE.md`;
4. inspeccionar repositorio real.

## 4. Repositorio esperado a verificar

```text
J:\AgenteForense\AgenteForense
```

Verificar:

- `git status`;
- `git branch`;
- `git log -1`;
- `git remote -v`;
- `.gitignore`;
- ausencia/presencia real de código;
- ausencia/presencia real de tests;
- que `casos/` no esté versionado.

No asumir valores históricos si el estado real difiere.

## 5. Protección absoluta

No modificar ni recorrer recursivamente evidencia real dentro de `casos/`.

No ejecutar:

- `ewfacquire`;
- `ewfverify`;
- AXIOM;
- OCR;
- Ollama;
- RAR;
- acceso a `PhysicalDrive`;
- operaciones de adquisición;
- operaciones de verificación.

## 6. Investigar entorno Python

Ejecutar y registrar:

```text
python --version
py --version
py -0p
```

Identificar intérprete real.

Crear `.venv` solo si corresponde y sin tocar herramientas externas.

## 7. Estructura mínima nueva

Crear únicamente si no existe:

```text
src\
  agente_forense\
    __init__.py
    __main__.py
    core\
      __init__.py
      errors.py
      states.py
    config\
      __init__.py
      paths.py

tests\
  __init__.py
  test_imports.py
  test_safety_baseline.py
```

## 8. Entry point

Debe funcionar:

```text
python -m agente_forense
```

Salida conceptual:

```text
AGENTE FORENSE
Reconstruction baseline initialized.
No forensic operation executed.
```

No debe iniciar operaciones reales.

## 9. Excepciones mínimas

Implementar:

```text
AgenteForenseError
ConfigurationError
SafetyViolationError
```

## 10. Estados mínimos

Implementar únicamente estados de bootstrap:

```text
INITIALIZING
READY
FAILED
ABORTED
```

No implementar todavía la máquina completa de estados del producto.

## 11. Configuración de rutas

Centralizar las rutas conocidas/configurables.

Separar como mínimo:

- repository root;
- cases root;
- EWF tools root;
- Ollama/models root;
- future file-store root.

No dispersar rutas hardcodeadas por el código.

### Discrepancia histórica G: / J:

Investigar.

No corregir documentación histórica silenciosamente.

Registrar cuál es la ruta efectiva actual.

## 12. Tests nuevos

La nueva suite comienza en 0.

Agregar tests que validen al menos:

- import del paquete;
- entry point;
- rutas sin tocar `casos/`;
- ausencia de operación forense;
- `.gitignore` protege artefactos sensibles;
- configuración falla de forma explícita si una ruta crítica es inválida.

No usar los conteos de tests históricos como baseline actual.

## 13. RECONSTRUCTION_STATUS.md

Crear con:

```text
SOURCE_CODE_LOST = true
TEST_SUITE_LOST = true
REIMPLEMENTATION_MODE = FROM_SCRATCH
CURRENT_REPOSITORY = ...
CURRENT_BRANCH = ...
CURRENT_COMMIT = ...
PYTHON_VERSION = ...
CASES_PROTECTED = true
FORENSIC_OPERATIONS_EXECUTED = false
STATUS = RECONSTRUCTION_BASELINE_READY / FAILED
```

## 14. Revisión Git

Antes de cerrar:

- ejecutar tests;
- `git status`;
- revisar archivos staged;
- confirmar que no haya evidencia;
- confirmar que no haya E01;
- confirmar que no haya secretos;
- confirmar que no haya `.env`;
- confirmar que no haya credenciales PostgreSQL.

## 15. PostgreSQL

NO implementar PostgreSQL en R00.

Solo puede registrarse como requisito futuro:

```text
PERSISTENCE_TARGET = POSTGRESQL
```

La versión/configuración real se investigará en R01.

## 16. Web localhost

NO implementar servidor web en R00.

Solo registrar:

```text
UI_TARGET = LOCALHOST_WEB
```

## 17. OpenClaw

NO integrar OpenClaw en R00.

La decisión sobre runtime del agente se hará después de investigación dedicada.

## 18. Criterio de cierre

R00 se considera completo si:

- estado real del repositorio documentado;
- Python real documentado;
- paquete mínimo nuevo funciona;
- suite nueva existe y pasa;
- configuración está centralizada;
- `casos/` permanece protegido;
- ninguna operación forense fue ejecutada;
- `RECONSTRUCTION_STATUS.md` existe;
- Git no incluye evidencia/secretos;
- arquitectura futura no queda bloqueada.

Estado final:

```text
RECONSTRUCTION_BASELINE_READY
```

## 19. No iniciar R01

TRAE debe detenerse después del reporte final.

R01 solo se redactará después de revisar el resultado real de R00.

## 20. Reporte final obligatorio

```text
SPRINT R00:
COMPLETADO / INCOMPLETO

REPOSITORIO:
...

BRANCH:
...

COMMIT:
...

ESTADO GIT:
...

SOURCE CODE PREVIO:
AUSENTE / ENCONTRADO

TEST SUITE PREVIA:
AUSENTE / ENCONTRADA

PYTHON:
...

VENV:
...

RUTAS:
...

DISCREPANCIA G:/J::
...

ARCHIVOS CREADOS:
...

ARCHIVOS MODIFICADOS:
...

TESTS NUEVOS:
...

RESULTADO TESTS:
...

CASOS/ MODIFICADO:
NO / SI

EVIDENCIA LEÍDA:
NO / SI

PHYSICALDRIVE:
NO / SI

EWFACQUIRE:
NO / SI

EWFVERIFY:
NO / SI

AXIOM:
NO / SI

OLLAMA:
NO / SI

POSTGRESQL MODIFICADO:
NO / SI

SERVIDOR WEB INICIADO:
NO / SI

RIESGOS / LIMITACIONES:
...

ESTADO:
RECONSTRUCTION_BASELINE_READY / FAILED
```
