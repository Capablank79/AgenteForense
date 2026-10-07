# SPRINT_R00 — Reinicialización técnica controlada desde cero

## 1. OBJETIVO

Iniciar formalmente la reconstrucción del proyecto **AGENTE FORENSE** desde cero después de la pérdida total del código fuente y de la suite de tests anterior.

El proyecto dispone actualmente de:

- documentación normativa recuperada;
- Sprints históricos recuperados;
- repositorio Git inicializado;
- baseline documental publicado en GitHub;
- árbol de casos/evidencia existente y excluido de Git;
- **ningún código Python recuperado**;
- **ninguna suite de tests recuperada**.

Por tanto:

```text
SOURCE_CODE_LOST = true
TEST_SUITE_LOST = true
REIMPLEMENTATION_MODE = FROM_SCRATCH
```

Este Sprint NO debe intentar recrear archivos perdidos por memoria, inferencia o supuestos.

Debe construir exclusivamente el **nuevo baseline técnico mínimo** sobre el cual se desarrollarán los siguientes Sprints de reconstrucción.

---

# 2. AUTORIDAD DOCUMENTAL

Antes de realizar cualquier modificación, leer completamente:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
```

Después revisar los Sprints históricos recuperados, especialmente:

```text
SPRINT_01.md
SPRINT_02.md
SPRINT_02_5.md
SPRINT_03.md
SPRINT_03_5_VALIDACION_REAL.md
SPRINT_04.md
SPRINT_04_1_RECONCILIACION_VERIFICACION.md
SPRINT_04_5_MODELO_JERARQUICO_RUC_NUE_ESPECIE_DSM.md
SPRINT_05_AGENTE_IDENTIFICACION_FOTOGRAFIAS.md
SPRINT_05A_INTEGRACION_FLUJO_NUEVA_ADQUISICION.md
SPRINT_05_1_IDENTIFICACION_ASISTIDA_WINDOWS_OCR_QWEN.md
```

Los Sprints anteriores son:

```text
FUENTE HISTÓRICA DE REQUISITOS
FUENTE DE DECISIONES TÉCNICAS
FUENTE DE ERRORES YA CORREGIDOS
FUENTE DE REGLAS DE SEGURIDAD
```

No son:

```text
CÓDIGO EXISTENTE
TESTS EXISTENTES
ESTADO DE IMPLEMENTACIÓN ACTUAL
```

---

# 3. REGLA DE RECONSTRUCCIÓN

No reconstruir deliberadamente arquitecturas históricas que posteriormente fueron sustituidas.

La reconstrucción debe incorporar desde el comienzo las decisiones que quedaron consolidadas en fases posteriores, siempre que no entren en conflicto con `PROMPT_MAESTRO.md`.

Ejemplo:

No reconstruir primero una estructura antigua de caso para migrarla después.

Preparar desde el nuevo diseño la arquitectura vigente:

```text
RUC
└── NUE
    └── ESPECIE
        └── DSM
```

La implementación funcional de dicha jerarquía NO pertenece necesariamente a R00.

R00 debe únicamente evitar decisiones arquitectónicas que impidan implementarla después.

---

# 4. ESTADO GIT DE PARTIDA

Baseline oficial recuperado:

```text
Repositorio local:
J:\AgenteForense\AgenteForense

Remoto:
https://github.com/Capablank79/AgenteForense.git

Rama:
main

Commit baseline documental:
b9f3f97

Estado:
GIT_BASELINE_RECOVERED_AND_PUSHED
```

Antes de modificar:

```powershell
git status
git branch --show-current
git remote -v
git log -1 --oneline
```

Resultado esperado:

```text
branch = main
working tree = clean
HEAD incluye b9f3f97 o un descendiente legítimo
origin apunta al repositorio oficial
```

Si alguno de estos datos no coincide:

```text
DETENER
DOCUMENTAR
NO MODIFICAR TODAVÍA
```

---

# 5. DISCREPANCIA DE RUTAS G: → J:

La documentación histórica contiene referencias a:

```text
G:\AgenteForense
```

El entorno recuperado actual informado es:

```text
J:\AgenteForense\AgenteForense
```

Esta discrepancia debe verificarse en el entorno real.

Antes de modificar rutas:

1. comprobar que existe:

```text
J:\AgenteForense\AgenteForense
```

2. comprobar que es el repositorio Git actual;

3. comprobar ubicación real de:

```text
ewftools-x64
OllamaModels
casos
```

4. comprobar si `G:\AgenteForense` todavía existe;

5. distinguir claramente:

```text
PROJECT_REPOSITORY_ROOT
FORENSIC_TOOLS_ROOT
OLLAMA_MODELS_ROOT
CASE_DATA_ROOT
```

No asumir que todos deben estar dentro del repositorio.

---

# 6. ACTUALIZACIÓN DEL PROMPT MAESTRO

Si la inspección real confirma que el proyecto operativo fue trasladado definitivamente desde `G:` hacia `J:`, actualizar `PROMPT_MAESTRO.md` para que no declare como vigente una ruta inexistente u obsoleta.

La modificación debe:

- conservar el historial conceptual;
- documentar el cambio de entorno;
- no alterar reglas forenses;
- no cambiar silenciosamente rutas de herramientas que no hayan sido verificadas;
- diferenciar repositorio, herramientas, modelos y casos cuando residan en ubicaciones distintas.

Nunca reemplazar globalmente `G:\` por `J:\` mediante búsqueda/reemplazo indiscriminado.

Muchas referencias `G:\` pertenecen a evidencia histórica de Sprints anteriores y deben permanecer como tales.

---

# 7. PROTECCIÓN ABSOLUTA DE `casos\`

Existe un árbol real:

```text
casos\
```

que puede contener información de casos y evidencia.

Regla para R00:

```text
NO LEER CONTENIDO FORENSE
NO MODIFICAR
NO RENOMBRAR
NO MOVER
NO BORRAR
NO HASHEAR MASIVAMENTE
NO INDEXAR
NO INCLUIR EN TESTS
NO VERSIONAR
```

Se permite únicamente comprobar de manera no intrusiva que:

```text
casos\
```

está excluido por `.gitignore`.

No recorrer recursivamente el contenido para este Sprint.

---

# 8. VALIDACIÓN DE `.gitignore`

Confirmar que al menos continúan excluidos:

```gitignore
casos/
.pytest_cache/
__pycache__/
*.pyc
.venv/
venv/
.env

*.E01
*.E02
*.Ex01
*.raw
*.dd
*.img

*.log
```

No eliminar exclusiones de evidencia.

Agregar únicamente exclusiones de desarrollo que estén técnicamente justificadas.

---

# 9. INVESTIGACIÓN DEL ENTORNO PYTHON

No asumir versión de Python.

Ejecutar operaciones no destructivas para conocer el entorno real:

```powershell
python --version
py --version
py -0p
```

cuando estén disponibles.

Registrar:

```text
python_version
python_executable
launcher_available
architecture si puede determinarse de forma fiable
```

No instalar automáticamente una versión distinta de Python.

Si no existe un Python utilizable:

```text
PYTHON_RUNTIME_UNAVAILABLE
```

y detener la creación de código hasta resolverlo.

---

# 10. GESTIÓN DE DEPENDENCIAS

R00 debe utilizar el mínimo de dependencias posible.

No instalar todavía:

```text
Ollama SDK
OCR libraries
computer vision libraries
Magnet AXIOM integrations
EWF Python wrappers
GUI frameworks
database engines
web frameworks
```

Para el baseline inicial, utilizar preferentemente:

```text
Python standard library
pytest
```

solo si `pytest` está realmente disponible o se autoriza instalarlo en el entorno de desarrollo.

No modificar herramientas forenses para satisfacer dependencias del proyecto.

---

# 11. ENTORNO VIRTUAL

Preferir un entorno virtual local de desarrollo:

```text
.venv\
```

siempre excluido de Git.

No utilizar el Python del sistema para instalar dependencias globalmente salvo necesidad técnica explícitamente justificada.

Registrar:

```text
venv_created
python_version
pip_version
```

No introducir gestores adicionales sin necesidad.

---

# 12. NUEVA ESTRUCTURA DE CÓDIGO

Crear un baseline modular desde cero.

Estructura mínima recomendada:

```text
J:\AgenteForense\AgenteForense\
│
├── src\
│   └── agente_forense\
│       ├── __init__.py
│       ├── __main__.py
│       ├── core\
│       │   ├── __init__.py
│       │   ├── errors.py
│       │   └── states.py
│       └── config\
│           ├── __init__.py
│           └── paths.py
│
├── tests\
│   ├── __init__.py
│   ├── test_imports.py
│   └── test_safety_baseline.py
│
├── PROMPT_MAESTRO.md
├── REGLA_PERMANENTE_PRE_SPRINT.md
├── SPRINT_*.md
└── .gitignore
```

Los nombres pueden ajustarse si existe una razón técnica mejor.

No crear todavía módulos funcionales de:

```text
disks
acquisition
verification
identification
axiom
results
report
ollama
ocr
```

salvo interfaces mínimas absolutamente necesarias para el baseline.

---

# 13. PACKAGE ROOT

Utilizar:

```text
src\agente_forense
```

como package principal.

Objetivo:

- evitar imports accidentales desde el directorio de trabajo;
- mantener separación entre código y tests;
- preparar empaquetado futuro;
- evitar módulos monolíticos.

---

# 14. ENTRYPOINT

Crear únicamente un entrypoint mínimo no forense:

```text
python -m agente_forense
```

Debe poder mostrar algo equivalente a:

```text
AGENTE FORENSE
Baseline de reconstrucción inicializado.
No se ejecutará ninguna operación forense.
```

No debe:

- detectar discos;
- abrir PhysicalDrive;
- inspeccionar casos;
- ejecutar PowerShell forense;
- ejecutar ewfacquire;
- ejecutar ewfverify;
- ejecutar Ollama;
- ejecutar OCR;
- modificar filesystem fuera del entorno controlado del proyecto.

---

# 15. MODELO DE ESTADOS BASE

Crear únicamente los estados genéricos necesarios para soportar desarrollo posterior.

Ejemplo mínimo:

```text
INITIALIZING
READY
FAILED
ABORTED
```

No recrear todavía toda la máquina histórica si no existe funcionalidad que la utilice.

Los estados específicos deben incorporarse cuando se implemente cada módulo.

---

# 16. EXCEPCIONES BASE

Crear jerarquía mínima explícita, por ejemplo:

```text
AgenteForenseError
ConfigurationError
SafetyViolationError
```

No llenar anticipadamente el proyecto de excepciones futuras.

---

# 17. CONFIGURACIÓN DE RUTAS

No hardcodear de nuevo rutas globales dispersas por los módulos.

Crear un punto central para configuración/rutas.

Debe diferenciar, conceptualmente:

```text
repository_root
case_data_root
ewf_tools_root
ollama_models_root
```

Los valores reales solo deben introducirse después de verificarlos.

No asumir que:

```text
repository_root == case_data_root
```

ni que herramientas externas pertenezcan al repositorio Git.

---

# 18. NINGÚN ACCESO A PHYSICALDRIVE

R00 tiene prohibido abrir:

```text
\\.\PhysicalDriveN
```

incluso en modo lectura.

No ejecutar todavía:

```powershell
Get-Disk
Get-Partition
Get-Volume
```

salvo que una comprobación puramente ambiental sea realmente necesaria y esté justificada.

La detección forense de discos pertenecerá a un Sprint posterior.

---

# 19. NINGUNA HERRAMIENTA FORENSE

R00 NO debe ejecutar:

```text
ewfacquire
ewfverify
Magnet AXIOM
FTK Imager
```

Tampoco debe invocar funciones equivalentes.

La mera comprobación de existencia de directorios de herramientas puede hacerse si es necesaria para reconciliar rutas, pero no ejecutar operaciones forenses.

---

# 20. NINGÚN OCR / OLLAMA

R00 NO debe ejecutar:

```text
Windows OCR
Ollama
qwen2.5:3b
```

La documentación histórica sobre OCR/Qwen será usada cuando corresponda reconstruir el Agente de Identificación.

No adelantar esa integración.

---

# 21. BASELINE DE TESTS

Como la suite anterior se perdió:

```text
PREVIOUS_TEST_COUNT = 0
```

No afirmar:

```text
160 passed
195 passed
206 passed
```

como baseline actual.

Esas cifras son únicamente antecedentes históricos.

R00 debe crear la **nueva suite de reconstrucción**.

---

# 22. TESTS OBLIGATORIOS DE R00

Crear tests mínimos para comprobar:

### Test 1 — Import principal

```text
import agente_forense
```

debe funcionar.

### Test 2 — Entry point

La ejecución controlada del entrypoint debe finalizar sin operaciones forenses.

### Test 3 — Estados base

Los estados mínimos definidos son accesibles y deterministas.

### Test 4 — Excepciones base

Las excepciones personalizadas heredan correctamente de la excepción base del proyecto.

### Test 5 — Protección de rutas de casos

La configuración no debe tratar `casos\` como directorio de código o tests.

### Test 6 — Sin artefactos forenses en Git

Comprobar mediante Git que no estén versionados archivos:

```text
*.E01
*.E02
*.Ex01
*.raw
*.dd
*.img
```

### Test 7 — `casos/` fuera de Git

Comprobar que ningún archivo bajo:

```text
casos/
```

figure en `git ls-files`.

### Test 8 — Ninguna dependencia forense

La importación del package base no debe requerir:

```text
ewfacquire
ewfverify
Ollama
OCR
AXIOM
```

### Test 9 — Smoke test

La suite mínima completa debe pasar desde un checkout limpio con el entorno configurado.

---

# 23. NO INVENTAR TESTS HISTÓRICOS

No intentar reconstruir los tests perdidos afirmando que son los originales.

Cualquier prueba creada desde este momento pertenece a:

```text
RECONSTRUCTION_TEST_SUITE
```

Debe quedar claramente distinguida de:

```text
LOST_HISTORICAL_TEST_SUITE
```

---

# 24. DOCUMENTACIÓN DEL ESTADO DE RECONSTRUCCIÓN

Crear un archivo técnico nuevo, por ejemplo:

```text
RECONSTRUCTION_STATUS.md
```

Debe registrar:

```text
reconstruction_mode: FROM_SCRATCH
source_code_recovered: false
historical_tests_recovered: false
documentation_recovered: true
git_baseline_commit: b9f3f97
repository_remote: https://github.com/Capablank79/AgenteForense.git
current_reconstruction_sprint: R00
```

Además:

- fecha/hora;
- Python detectado;
- entorno virtual;
- número de tests nuevos;
- resultado de tests;
- rutas reales verificadas;
- discrepancias pendientes.

No incluir secretos.

No incluir datos contenidos dentro de casos reales.

---

# 25. SPRINTS HISTÓRICOS INMUTABLES

No modificar los Sprints históricos para hacer parecer que fueron ejecutados en esta reconstrucción.

Conservarlos como evidencia documental histórica.

Los nuevos Sprints usarán nomenclatura:

```text
SPRINT_R00.md
SPRINT_R01.md
SPRINT_R02.md
...
```

---

# 26. REGLAS ARQUITECTÓNICAS YA CONOCIDAS

Aunque R00 no las implemente, la nueva base no debe impedir las decisiones consolidadas siguientes:

```text
RUC
└── NUE
    └── ESPECIE
        └── DSM
```

Para casos nuevos futuros:

```text
schema_version = 2
```

Debe poder soportarse posteriormente:

```text
SELF_STORAGE
CONTAINED_STORAGE
```

y la nomenclatura:

```text
NUE_<NUE>_ESPECIE<n>_DSM<m>
```

No implementar todavía toda esa lógica.

Solo evitar crear una arquitectura incompatible con ella.

---

# 27. PERSISTENCIA FUTURA

Preparar la arquitectura para que futuras escrituras críticas utilicen persistencia atómica:

```text
archivo temporal
→ flush
→ fsync
→ os.replace
```

R00 puede crear una utilidad solo si existe una necesidad real dentro del Sprint.

No implementar funcionalidades futuras únicamente “por si acaso”.

---

# 28. AUDITORÍA

R00 debe establecer únicamente una base de logging de aplicación si es necesaria.

No simular un audit trail forense que todavía no existe.

Nunca registrar:

- tokens;
- contraseñas;
- credenciales;
- secretos;
- contenido de evidencia.

La auditoría forense completa se implementará progresivamente junto con operaciones que realmente requieran trazabilidad.

---

# 29. SEGURIDAD

Durante R00 está prohibido:

```text
abrir PhysicalDrive
Set-Disk
DiskPart
CHKDSK
formatear
inicializar discos
montar evidencia
desmontar evidencia
escribir en evidencia
ewfacquire
ewfverify
AXIOM
FTK
OCR
Ollama
leer recursivamente casos\
modificar casos\
mover casos\
versionar casos\
```

---

# 30. CRITERIO FAIL-CLOSED

Si durante R00 se detecta una discrepancia material sobre:

- raíz real del proyecto;
- ubicación de herramientas;
- Python disponible;
- estado Git;
- inclusión accidental de evidencia;
- estructura real del repositorio;

detener la parte dependiente de esa información.

No inventar una respuesta para continuar.

---

# 31. CRITERIOS DE TERMINADO

SPRINT_R00 se considera **COMPLETO** únicamente cuando:

```text
[ ] PROMPT_MAESTRO.md leído completamente
[ ] REGLA_PERMANENTE_PRE_SPRINT.md leída completamente
[ ] Sprints históricos relevantes revisados
[ ] estado Git verificado
[ ] commit baseline b9f3f97 reconocido como antecedente
[ ] origin verificado
[ ] discrepancia G: / J: investigada
[ ] rutas reales documentadas
[ ] PROMPT_MAESTRO reconciliado si corresponde
[ ] Python real identificado
[ ] entorno de desarrollo definido
[ ] src\ creado desde cero
[ ] tests\ creado desde cero
[ ] package agente_forense creado
[ ] entrypoint mínimo funciona
[ ] estados base creados
[ ] excepciones base creadas
[ ] configuración central de rutas preparada
[ ] nueva suite de reconstrucción ejecutada
[ ] todos los tests R00 pasan
[ ] casos\ sigue excluido de Git
[ ] ningún artefacto de evidencia está versionado
[ ] ningún PhysicalDrive fue abierto
[ ] ninguna herramienta forense fue ejecutada
[ ] ninguna evidencia fue modificada
[ ] RECONSTRUCTION_STATUS.md creado
[ ] working tree revisado antes de commit
```

---

# 32. COMMIT DEL SPRINT

Solo después de cumplir los criterios de terminado:

revisar:

```powershell
git status --short
git diff
git diff --cached
git ls-files
```

Confirmar específicamente:

```text
casos/ NO VERSIONADO
E01/RAW/DD/IMG NO VERSIONADOS
secretos NO VERSIONADOS
```

Crear un único commit coherente para R00.

Mensaje recomendado:

```text
Sprint R00: inicializa reconstrucción técnica desde cero
```

Después:

```powershell
git push origin main
```

No hacer push si el staging contiene evidencia, secretos o archivos no revisados.

---

# 33. ESTADO FINAL ESPERADO

Si todo pasa:

```text
RECONSTRUCTION_BASELINE_READY
```

Significa únicamente:

- repositorio técnico inicializado;
- package Python mínimo creado;
- nueva suite de tests creada;
- entorno documentado;
- reglas de seguridad preservadas;
- ninguna funcionalidad forense todavía implementada.

NO significa:

```text
DISK_DETECTION_READY
ACQUISITION_READY
IDENTIFICATION_READY
AXIOM_READY
REPORT_READY
```

---

# 34. SIGUIENTE SPRINT

No iniciar automáticamente el siguiente Sprint.

El siguiente Sprint deberá diseñarse a partir del resultado real de R00.

Candidato conceptual:

```text
SPRINT_R01
Detección y clasificación segura de discos físicos
```

pero sus requisitos definitivos deben redactarse únicamente después de recibir y revisar el informe final real de R00, conforme a `REGLA_PERMANENTE_PRE_SPRINT.md`.

---

# 35. REPORTE FINAL OBLIGATORIO

Al terminar, entregar exactamente una sección equivalente a:

```text
SPRINT R00:
COMPLETADO / INCOMPLETO

MODO:
FROM_SCRATCH

GIT BASELINE:
...

REPOSITORIO:
...

RAMA:
...

REMOTO:
...

DISCREPANCIA G:/J::
...

RUTAS REALES VERIFICADAS:
Repository:
Cases:
EWF Tools:
Ollama Models:

PROMPT_MAESTRO:
MODIFICADO / NO MODIFICADO
Razón:

PYTHON:
Versión:
Ejecutable:

ENTORNO VIRTUAL:
...

ESTRUCTURA CREADA:
...

ARCHIVOS CREADOS:
...

ARCHIVOS MODIFICADOS:
...

TEST SUITE HISTÓRICA:
LOST

NUEVA TEST SUITE:
Cantidad:
Resultado:

PHYSICALDRIVE ACCEDIDO:
NO

EWFACQUIRE:
NO

EWFVERIFY:
NO

AXIOM:
NO

OLLAMA:
NO

OCR:
NO

CASOS MODIFICADOS:
NO

CASOS VERSIONADOS:
NO

ARTEFACTOS FORENSES VERSIONADOS:
NO

SECRETOS DETECTADOS:
...

GIT STATUS FINAL:
...

COMMIT:
...

PUSH:
...

RIESGOS / PENDIENTES:
...

ESTADO FINAL:
RECONSTRUCTION_BASELINE_READY / INCOMPLETE
```

Si cualquier criterio material falta, indicar exactamente cuál.

---

# 36. INSTRUCCIÓN FINAL PARA TRAE

TRAE:

1. trabaja desde la realidad actual, no desde el código perdido;
2. lee completamente `PROMPT_MAESTRO.md`;
3. lee completamente `REGLA_PERMANENTE_PRE_SPRINT.md`;
4. revisa la documentación histórica;
5. confirma Git y filesystem antes de modificar;
6. investiga la discrepancia `G:` / `J:`;
7. no hagas reemplazos masivos de rutas;
8. identifica el Python realmente instalado;
9. crea la nueva base de código desde cero;
10. crea la nueva suite de tests desde cero;
11. no recrees código histórico inexistente como si fuera recuperado;
12. no accedas a evidencia;
13. no abras PhysicalDrive;
14. no ejecutes herramientas forenses;
15. mantén `casos/` fuera de Git;
16. ejecuta todos los tests nuevos;
17. inspecciona staging;
18. documenta el estado;
19. commit solo con baseline técnico seguro;
20. push a `main`;
21. entrega el reporte final;
22. NO inicies R01.

Comienza ahora.