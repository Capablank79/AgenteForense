# SPRINT_R02 — Investigación y definición de la plataforma Web Localhost

## 1. Objetivo

Investigar el entorno Python/web REAL disponible en la estación Windows y definir, con evidencia técnica, la plataforma web local que utilizará el AGENTE FORENSE.

Este sprint NO implementa todavía la interfaz web productiva.

Su objetivo es decidir de forma verificable:

- framework backend/API;
- servidor ASGI/WSGI;
- estrategia de frontend;
- mecanismo de carga de archivos;
- integración con PostgreSQL existente;
- binding estricto a localhost;
- manejo de sesiones/errores;
- arquitectura de API;
- pruebas;
- estrategia para trabajos largos;
- límites de seguridad.

Resultado esperado:

```text
LOCAL_WEB_STACK_VERIFIED
```

o:

```text
LOCAL_WEB_STACK_BLOCKED
```

## 2. Documentación obligatoria

Antes de cualquier decisión, TRAE debe leer completos:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
ROADMAP_RECONSTRUCCION_AGENTE_FORENSE.md
SPRINT_R00.md
SPRINT_R01.md
SPRINT_R01_1.md
RECONSTRUCTION_STATUS.md
POSTGRESQL_CAPABILITIES.md
PERSISTENCE_ARCHITECTURE.md
SPRINT_R02.md
```

También debe revisar los reportes finales reales de R00, R01 y R01.1.

No utilizar sprints históricos previos a la reconstrucción como baseline de código.

## 3. Baseline vigente

Estado mínimo esperado:

```text
PYTHON:
3.10.11

POSTGRESQL:
18.6

DB HOST:
127.0.0.1

DB PORT:
5433

DATABASE:
agente_forense_db

APPLICATION ROLE:
agente_forense_app

PERSISTENCE:
READY

TESTS:
45 passed
```

Antes de investigar:

```text
git status
git branch --show-current
git log -1 --oneline
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pytest
```

Registrar resultados reales.

Si existe regresión:

```text
DETENER
DOCUMENTAR
NO CONTINUAR
```

## 4. Regla principal de este sprint

NO elegir FastAPI, Flask, Django, Starlette, Uvicorn, Hypercorn, Waitress, React, Vue, HTMX, Jinja2 u otra tecnología por preferencia o intuición.

Primero investigar:

1. qué está instalado;
2. versiones;
3. compatibilidad con Python 3.10;
4. comportamiento real en Windows;
5. soporte para localhost;
6. carga de archivos;
7. testing;
8. integración PostgreSQL;
9. manejo de tareas largas;
10. complejidad operativa;
11. dependencias necesarias;
12. mantenimiento.

Solo después emitir recomendación.

## 5. Inventario Python real

Dentro de `.venv`, registrar como mínimo:

```text
python version
pip version
installed packages
```

Buscar específicamente:

```text
fastapi
starlette
uvicorn
flask
django
jinja2
werkzeug
waitress
hypercorn
httpx
requests
python-multipart
pydantic
sqlalchemy
psycopg
pytest
pytest-asyncio
```

No instalar paquetes en R02.

Si no existen, documentar:

```text
NOT_INSTALLED
```

Eso no implica fallo.

## 6. Evaluar backend/API

Comparar candidaturas razonables para este proyecto.

Como mínimo evaluar, si son compatibles con el entorno actual:

```text
FastAPI + Starlette + Uvicorn
Flask + Waitress
Django
```

La comparación debe considerar:

- Python 3.10;
- Windows;
- localhost;
- tipado;
- validación de datos;
- documentación OpenAPI;
- carga de archivos;
- testing;
- modularidad;
- integración SQLAlchemy/psycopg;
- endpoints async/sync;
- long-running jobs;
- facilidad de mantener;
- dependencia total;
- superficie de seguridad;
- adecuación a una aplicación local de un solo puesto.

No implementar las tres.

Elegir una sola estrategia recomendada.

## 7. Frontend

Investigar y comparar al menos:

```text
server-rendered HTML + Jinja2
server-rendered HTML + HTMX
SPA separada (React/Vue/etc.)
```

El objetivo no es usar la tecnología más compleja.

Priorizar:

- operación local;
- poca infraestructura;
- despliegue sencillo;
- formularios;
- dashboard;
- tablas;
- subida de archivos;
- estados en tiempo real;
- panel de auditoría;
- futura interfaz conversacional;
- mantenibilidad.

La UI final debe ser web, no CLI.

## 8. Binding y exposición

La aplicación futura debe escuchar exclusivamente en loopback por defecto.

Investigar comportamiento real de la plataforma candidata con:

```text
127.0.0.1
localhost
::1
0.0.0.0
```

La configuración productiva futura debe impedir por defecto:

```text
0.0.0.0
```

No abrir firewall.

No crear regla de red.

No exponer servicio a LAN.

## 9. Puerto de la aplicación

Definir una estrategia de puerto web.

No reutilizar:

```text
5432
5433
```

Evaluar un puerto local configurable, por ejemplo dentro de rango no privilegiado.

NO fijar número definitivo sin verificar que no colisiona en la máquina.

Realizar inspección local de puertos candidatos.

La futura configuración deberá permitir:

```text
AGENTE_FORENSE_WEB_HOST=127.0.0.1
AGENTE_FORENSE_WEB_PORT=<verified>
```

## 10. Integración con PostgreSQL

Confirmar que el framework seleccionado puede consumir la capa de persistencia existente sin:

- duplicar modelos;
- acoplar SQL directamente a rutas HTTP;
- usar credenciales `postgres`;
- usar puerto 5432;
- saltarse repositories;
- romper transacciones.

La web debe usar:

```text
agente_forense_app
127.0.0.1:5433
```

## 11. Arquitectura objetivo

Proponer una arquitectura concreta para R02.1.

Debe mantener separación:

```text
WEB UI
   ↓
HTTP/API
   ↓
APPLICATION SERVICES
   ↓
DOMAIN / ORCHESTRATOR
   ↓
REPOSITORIES
   ↓
POSTGRESQL + FILE STORE
```

No permitir:

```text
HTML route
→ SQL directo
```

ni:

```text
JavaScript
→ PostgreSQL
```

## 12. API inicial propuesta

Diseñar, sin implementar, endpoints iniciales equivalentes a:

```text
GET  /health
GET  /api/system/status
GET  /api/cases
GET  /api/cases/{id}
GET  /api/audit
```

Para futuros casos:

```text
POST /api/cases/draft
POST /api/files/stage
```

Pero R02 NO debe crear RUC real ni cargar evidencia real.

Definir contratos JSON conceptuales.

## 13. Health Check

El futuro `/health` debe distinguir al menos:

```text
application
database
filestore
```

No revelar:

- passwords;
- connection strings completas;
- filesystem sensible;
- stack traces;
- secretos.

Ejemplo conceptual:

```json
{
  "status": "ok",
  "database": "ok",
  "filestore": "ok"
}
```

## 14. Manejo de errores

Diseñar respuesta de error estructurada:

```text
error_code
message
request_id
details_safe
```

No exponer tracebacks al operador.

Tracebacks técnicos van a logs locales.

Compatible con regla del Prompt Maestro.

## 15. Carga de archivos

Investigar mecanismo real de multipart/upload de la plataforma seleccionada.

Diseñar controles futuros:

- tamaño máximo configurable;
- nombre original conservado en metadata;
- nombre almacenado seguro;
- hash SHA-256;
- streaming si corresponde;
- no sobrescritura;
- FileStore como única capa de persistencia física;
- validación de MIME/extensión como señal, no como verdad absoluta;
- path traversal bloqueado;
- staging temporal;
- limpieza controlada ante error.

No subir archivos reales en R02.

## 16. Sesiones y autenticación

El sistema es local, pero no asumir que "localhost = sin seguridad".

Investigar alternativas para futuro:

```text
sin login inicial para laboratorio mono-operador
login local
Windows identity/SSPI
session cookie local
```

No implementar autenticación todavía.

Emitir recomendación proporcional al uso esperado.

No incorporar OAuth/cloud.

## 17. Protección CSRF / formularios

Si la opción elegida usa cookies/forms server-side, investigar:

- CSRF;
- SameSite;
- HttpOnly;
- Secure en contexto localhost HTTP;
- comportamiento real.

No inventar protección que el stack no soporte.

## 18. Trabajos largos

El producto final tendrá operaciones que pueden durar horas:

```text
E01 acquisition
EWF verification
AXIOM processing
Portable generation
RAR
report generation
```

Investigar cómo la plataforma elegida coexistirá con un Job/State Engine persistente.

Regla:

```text
HTTP request
≠
lifetime del trabajo forense
```

La tarea no debe morir porque:

- se cierre el navegador;
- expire la request;
- se recargue la página.

R02 solo diseña este contrato.

No implementar worker todavía.

## 19. Actualización de progreso

Evaluar para R02.1/futuro:

```text
polling
Server-Sent Events
WebSocket
```

Elegir la opción inicial más simple y robusta para dashboard local.

No sobrearquitectar.

## 20. Interfaz inicial futura

Diseñar las pantallas mínimas:

```text
/
Dashboard

/cases
Casos

/cases/new
Nuevo caso / ingreso

/cases/{id}
Ficha del caso

/audit
Auditoría

/system
Estado del sistema
```

El futuro Dashboard debe poder mostrar:

```text
RUC
estado
NUE count
DSM count
última actividad
siguiente acción
errores/bloqueos
```

No implementar todavía `next_action` definitivo; corresponde al State Engine posterior.

## 21. Nuevo caso futuro

La UI debe prepararse para que el operador pueda:

```text
subir petitorio
subir fotografías
```

y más adelante el sistema extraiga:

```text
RUC
NUE
unidad solicitante
descripción
diligencia
```

No convertir ahora la UI en un formulario manual rígido que obligue a ingresar todos esos campos.

La arquitectura debe permitir:

```text
PETITORIO
→ OCR
→ CaseStructureDraft
→ revisión/corrección
→ persistencia
```

## 22. OpenClaw

NO integrar OpenClaw en R02.

La evaluación del runtime de agente queda para el sprint específico del roadmap.

La UI web debe diseñarse de forma que un agente futuro pueda utilizar los mismos application services/API sin reemplazar la lógica central.

## 23. Ollama / Qwen

NO ejecutar Ollama.

NO integrar Qwen.

Solo asegurar que la arquitectura web no impida agregar posteriormente un panel conversacional.

## 24. Investigación documental externa

Si una candidatura web no está instalada o su comportamiento/versionado es material para la decisión:

- consultar documentación oficial/primaria;
- registrar referencias en `WEB_STACK_CAPABILITIES.md`;
- no basarse exclusivamente en blogs.

Prioridad:

1. entorno local;
2. ayuda/versiones locales;
3. documentación oficial.

## 25. Entregable obligatorio

Crear:

```text
WEB_STACK_CAPABILITIES.md
```

Debe contener:

```text
PYTHON_VERSION
VENV
PACKAGES_OBSERVED

BACKEND_CANDIDATES
COMPARISON

SELECTED_BACKEND
RATIONALE

SELECTED_SERVER
RATIONALE

SELECTED_FRONTEND_STRATEGY
RATIONALE

LOCALHOST_BINDING
PORT_STRATEGY

POSTGRES_INTEGRATION

UPLOAD_STRATEGY

ERROR_MODEL

SESSION_STRATEGY

CSRF_STRATEGY

LONG_RUNNING_JOB_STRATEGY

PROGRESS_UPDATE_STRATEGY

INITIAL_ROUTES

INITIAL_API

DEPENDENCIES_REQUIRED_FOR_R02_1

SECURITY_NOTES

RISKS

BLOCKERS
```

## 26. No realizar

Prohibido en R02:

- instalar framework web;
- instalar servidor web;
- iniciar servidor;
- abrir puerto;
- cambiar firewall;
- exponer LAN;
- modificar PostgreSQL;
- crear tablas;
- crear casos;
- tocar `casos/`;
- leer evidencia;
- subir fotos reales;
- subir petitorio real;
- PhysicalDrive;
- ewfacquire;
- ewfverify;
- AXIOM;
- Ollama;
- RAR;
- Word;
- OpenClaw.

## 27. Tests

Antes:

```text
45 passed
```

o más si el baseline creció legítimamente.

R02 puede no agregar código.

Si crea utilidades de inspección:

- deben ser no invasivas;
- deben tener tests.

Al final:

```text
pytest
```

sin regresiones.

## 28. Criterio de aceptación

R02 queda COMPLETO si:

- baseline R01.1 permanece verde;
- stack local inventariado;
- candidatos comparados;
- backend seleccionado con justificación;
- servidor seleccionado;
- estrategia frontend seleccionada;
- binding localhost definido;
- estrategia de puerto definida;
- integración PostgreSQL definida;
- estrategia de uploads definida;
- estrategia de sesiones/CSRF definida;
- contrato de long-running jobs definido;
- estrategia de actualización de progreso definida;
- arquitectura API/UI definida;
- dependencias exactas para R02.1 identificadas;
- ninguna herramienta/servicio fue modificado;
- no se inició servidor web;
- `casos/` intacto;
- `WEB_STACK_CAPABILITIES.md` creado;
- tests finales verdes.

Estado:

```text
LOCAL_WEB_STACK_VERIFIED
```

Si falta información material:

```text
LOCAL_WEB_STACK_BLOCKED
```

## 29. Después de R02

NO iniciar implementación web automáticamente.

Primero entregar reporte final.

Después de revisión se redactará:

```text
SPRINT_R02_1 — Implementación API + Web localhost
```

## 30. Reporte final obligatorio

```text
SPRINT R02:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE:
...

TESTS BEFORE:
...

PYTHON:
...

VENV:
...

PACKAGES:
...

BACKEND CANDIDATES:
...

SELECTED BACKEND:
...

SELECTED SERVER:
...

SELECTED FRONTEND:
...

LOCALHOST BINDING:
...

PORT STRATEGY:
...

POSTGRES INTEGRATION:
...

UPLOAD STRATEGY:
...

ERROR MODEL:
...

SESSION STRATEGY:
...

CSRF:
...

LONG RUNNING JOBS:
...

PROGRESS UPDATE:
...

INITIAL ROUTES:
...

INITIAL API:
...

DEPENDENCIES REQUIRED:
...

FILES CREATED:
...

FILES MODIFIED:
...

WEB SERVER STARTED:
NO / SI

POSTGRESQL MODIFIED:
NO / SI

CASOS/ MODIFIED:
NO / SI

EVIDENCE READ:
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

OPENCLAW:
NO / SI

TESTS FINAL:
...

RISKS:
...

BLOCKERS:
...

STATUS:
LOCAL_WEB_STACK_VERIFIED / LOCAL_WEB_STACK_BLOCKED
```

## 31. Instrucción final

TRAE:

1. lee documentación vigente;
2. valida baseline real;
3. inventaría el entorno web local;
4. compara frameworks sin instalar todavía;
5. consulta documentación oficial cuando corresponda;
6. selecciona stack mínimo y robusto;
7. define localhost, uploads, errores y jobs largos;
8. crea `WEB_STACK_CAPABILITIES.md`;
9. ejecuta tests;
10. entrega reporte;
11. detente;
12. NO inicies R02.1.

Comienza ahora.
