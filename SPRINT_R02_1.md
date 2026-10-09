# SPRINT_R02_1 — Implementación API + Web Localhost

## 1. Objetivo

Implementar la primera interfaz web funcional del AGENTE FORENSE sobre el stack ya investigado y validado en R02:

```text
FastAPI
Uvicorn
Jinja2
HTMX o Fetch API
PostgreSQL 18.6
SQLAlchemy 2.x
psycopg 3
```

La aplicación debe funcionar exclusivamente en:

```text
127.0.0.1:<puerto configurado>
```

con puerto inicial:

```text
8085
```

Este sprint implementa la base web, dashboard, API, health checks, navegación y cargas sintéticas/controladas.

NO debe todavía procesar petitorios reales, fotografías reales ni ejecutar operaciones forenses.

Estado esperado:

```text
LOCAL_WEB_FOUNDATION_READY
```

---

## 2. Documentación obligatoria

Antes de modificar código:

```text
PROMPT_MAESTRO.md
REGLA_PERMANENTE_PRE_SPRINT.md
ROADMAP_RECONSTRUCCION_AGENTE_FORENSE.md
SPRINT_R00.md
SPRINT_R01.md
SPRINT_R01_1.md
SPRINT_R02.md
RECONSTRUCTION_STATUS.md
POSTGRESQL_CAPABILITIES.md
PERSISTENCE_ARCHITECTURE.md
WEB_STACK_CAPABILITIES.md
SPRINT_R02_1.md
```

También revisar los reportes finales reales de R00, R01, R01.1 y R02.

---

## 3. Baseline

Esperado:

```text
PYTHON:
3.10.11

POSTGRESQL:
18.6

DB:
agente_forense_db

DB HOST:
127.0.0.1

DB PORT:
5433

TESTS:
45 passed
```

Antes de cambios:

```text
git status
git branch --show-current
git log -1 --oneline
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pytest
```

Registrar valores reales.

Si existe regresión:

```text
DETENER
DOCUMENTAR
NO IMPLEMENTAR
```

---

## 4. Dependencias Web

Instalar dentro de `.venv` únicamente:

```text
fastapi
uvicorn
jinja2
python-multipart
httpx
```

HTMX:

preferir inicialmente archivo JS local versionado si se decide utilizarlo.

NO depender de CDN en producción local.

Después de instalación:

```text
pip freeze
```

registrar versiones exactas.

No fijar versiones inventadas previamente.

Actualizar el mecanismo de dependencias del proyecto de forma reproducible.

---

## 5. Compatibilidad

Confirmar después de instalación:

- FastAPI funciona con Python 3.10.11;
- Uvicorn inicia correctamente en Windows;
- Jinja2 renderiza templates;
- `UploadFile` funciona;
- `python-multipart` procesa multipart;
- `httpx` funciona para tests.

No asumir funcionamiento hasta probarlo.

---

## 6. Arquitectura

Mantener separación:

```text
WEB
↓
APPLICATION SERVICES
↓
REPOSITORIES
↓
POSTGRESQL / FILESTORE
```

Prohibido:

```text
route -> SQL directo
template -> SQL
JS -> PostgreSQL
```

Crear paquete modular, por ejemplo:

```text
src/agente_forense/web/
    __init__.py
    app.py
    config.py
    dependencies.py
    errors.py
    routes/
        __init__.py
        pages.py
        api_health.py
        api_cases.py
        api_audit.py
        api_files.py
    templates/
        base.html
        dashboard.html
        cases.html
        case_detail.html
        case_new.html
        audit.html
        system.html
        error.html
    static/
        css/
        js/
```

Ajustar nombres solo si existe razón técnica clara.

---

## 7. Configuración Web

Agregar:

```text
AGENTE_FORENSE_WEB_HOST
AGENTE_FORENSE_WEB_PORT
```

Defaults:

```text
HOST=127.0.0.1
PORT=8085
```

Regla crítica:

```text
0.0.0.0
```

debe ser rechazado por configuración normal del producto.

También rechazar binding externo no autorizado.

La aplicación no debe abrir firewall.

---

## 8. App Factory

Preferir:

```python
create_app()
```

o equivalente.

Objetivo:

- testeable;
- dependencias inyectables;
- configuración desacoplada;
- evitar globals innecesarios.

---

## 9. Endpoint `/health`

Implementar:

```text
GET /health
```

Debe comprobar al menos:

```text
application
database
filestore
```

Respuesta ejemplo:

```json
{
  "status": "ok",
  "application": "ok",
  "database": "ok",
  "filestore": "ok"
}
```

No exponer:

- password;
- DSN completo;
- filesystem absoluto sensible;
- traceback;
- variables de entorno.

Si DB falla:

```text
HTTP 503
```

con error seguro.

---

## 10. `/api/system/status`

Implementar:

```text
GET /api/system/status
```

Puede mostrar información segura:

```text
application_version
python_version
database_status
database_version
web_host
web_port
```

No mostrar secretos.

---

## 11. Dashboard `/`

Implementar página HTML:

```text
/
```

Debe mostrar:

- nombre AGENTE FORENSE;
- estado aplicación;
- estado PostgreSQL;
- cantidad de casos;
- actividad reciente;
- accesos a Casos, Nuevo Caso, Auditoría, Sistema.

No crear lógica forense aún.

---

## 12. Casos

### `GET /cases`

Listar casos existentes en PostgreSQL.

Si DB está vacía:

mostrar estado vacío correctamente.

### `GET /cases/{id}`

Mostrar:

```text
RUC
estado
NUEs
species
DSMs
created_at
updated_at
```

solo si existen.

No inventar información.

### `GET /api/cases`

JSON estructurado.

### `GET /api/cases/{id}`

JSON estructurado.

No devolver secrets ni paths absolutos internos innecesarios.

---

## 13. Nuevo Caso `/cases/new`

Crear interfaz preliminar preparada para flujo futuro.

Debe incluir:

```text
PETITORIO
[ seleccionar archivo ]

FOTOGRAFÍAS
[ seleccionar archivos ]

RUC manual opcional
```

IMPORTANTE:

en R02.1 no se procesará OCR.

La UI debe indicar:

```text
Procesamiento automático del petitorio pendiente de sprint posterior.
```

No obligar todavía a llenar manualmente todos los campos.

---

## 14. Draft sintético

Implementar:

```text
POST /api/cases/draft
```

solo para datos sintéticos / tests.

Debe permitir construir un borrador mínimo sin crear todavía estructura forense definitiva.

No debe tocar evidencia real.

No debe crear carpetas reales de caso en `casos/`.

---

## 15. File Staging

Implementar:

```text
POST /api/files/stage
```

Solo para entorno de prueba/controlado en R02.1.

Pipeline:

```text
UploadFile
↓
staging temporal
↓
nombre seguro
↓
SHA-256
↓
FileStore de test
↓
metadata
```

No usar `bytes = await file.read()` para archivos potencialmente grandes si implica cargar todo a RAM.

Usar escritura por chunks/streaming.

Agregar límite de tamaño configurable.

---

## 16. Límite de Upload

Agregar:

```text
AGENTE_FORENSE_MAX_UPLOAD_BYTES
```

Elegir default conservador para desarrollo.

No fijar límite forense final todavía.

Si excede:

```text
HTTP 413
```

y limpiar archivo parcial.

---

## 17. Tipos permitidos en R02.1

Para pruebas:

```text
.txt
.pdf
.jpg
.jpeg
.png
```

La extensión/MIME solo es señal.

No confiar en MIME como evidencia de contenido.

No ejecutar parser ni OCR.

---

## 18. Staging

Usar directorio de staging separado de `casos/` para este sprint.

Ejemplo conceptual:

```text
runtime/staging/
```

o `%TEMP%`.

Debe estar excluido de Git.

No usar:

```text
casos/
```

todavía para uploads reales.

---

## 19. Limpieza

Si upload falla:

- cerrar stream;
- eliminar parcial de staging;
- no dejar metadata incoherente;
- registrar error seguro.

No borrar artefactos válidos existentes.

---

## 20. Auditoría Web

Implementar:

```text
GET /audit
GET /api/audit
```

Solo lectura.

Mostrar eventos disponibles en PostgreSQL.

No ofrecer DELETE.

No ofrecer UPDATE.

---

## 21. Sistema `/system`

Mostrar:

- versión aplicación;
- Python;
- estado DB;
- host/puerto web;
- filestore status;
- test/runtime mode.

No mostrar credenciales.

---

## 22. Error Model

Implementar modelo uniforme:

```json
{
  "error_code": "...",
  "message": "...",
  "request_id": "...",
  "details_safe": {}
}
```

Cada request debe poder tener `request_id`.

Errores inesperados:

- log técnico;
- respuesta genérica;
- sin traceback al navegador.

---

## 23. Logging

Agregar logging estructurado básico.

Registrar:

```text
request_id
method
path
status_code
duration
```

No registrar:

- passwords;
- body completo de uploads;
- tokens;
- secretos.

---

## 24. CSRF

Como todavía no hay operaciones destructivas productivas:

implementar protección para formularios state-changing si se habilitan.

Si se usa estrategia custom:

- documentarla;
- testearla.

No inventar falsa seguridad.

Si se decide postergar CSRF completo hasta que existan sesiones:

documentarlo explícitamente como limitación.

---

## 25. Headers

Configurar al menos cuando aplique:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy
```

No agregar políticas incompatibles sin probar.

---

## 26. No Cache para páginas sensibles

Evaluar y aplicar:

```text
Cache-Control: no-store
```

en páginas/API que muestren datos forenses.

---

## 27. HTMX / Fetch

Elegir una sola estrategia principal inicial.

Preferencia:

```text
server-rendered Jinja2
+
HTMX para interacciones pequeñas
```

si HTMX puede mantenerse localmente.

Si no:

```text
Fetch API
```

No agregar SPA.

---

## 28. Polling

Preparar contrato futuro:

```text
GET /api/jobs/{id}/status
```

pero NO implementar job engine todavía.

Puede existir placeholder `501/NOT_IMPLEMENTED` si es útil para contrato, aunque preferible no exponer endpoint hasta R04.

---

## 29. Uvicorn

Crear comando/script de arranque que fuerce:

```text
host=127.0.0.1
port=8085
```

o valores validados desde configuración.

NO usar:

```text
--host 0.0.0.0
```

por defecto.

No activar reload en modo operativo.

---

## 30. Smoke Test manual

Después de tests automáticos:

iniciar temporalmente servidor local:

```text
127.0.0.1:8085
```

Verificar:

```text
/
 /health
 /cases
 /audit
 /system
```

Luego detener servidor.

Confirmar que no escucha en:

```text
0.0.0.0
```

ni interfaz LAN.

---

## 31. Test de red

Verificar con herramientas locales:

```text
netstat
Get-NetTCPConnection
```

que el listener esté únicamente en loopback.

Registrar evidencia en reporte.

No abrir firewall.

---

## 32. Tests obligatorios

Mantener:

```text
45 baseline
```

Agregar como mínimo:

1. app factory;
2. web config host default 127.0.0.1;
3. port default 8085;
4. `0.0.0.0` rechazado;
5. host externo rechazado;
6. `/health` 200 con DB disponible;
7. `/health` no expone secreto;
8. `/health` 503 si DB falla;
9. `/api/system/status`;
10. dashboard render;
11. `/cases` render vacío;
12. `/api/cases` JSON;
13. case detail 404 seguro;
14. `/audit`;
15. `/api/audit`;
16. error model;
17. request_id;
18. traceback no expuesto;
19. upload pequeño válido;
20. upload supera límite -> 413;
21. path traversal bloqueado;
22. filename reservado bloqueado;
23. staging cleanup en error;
24. hash SHA-256 upload correcto;
25. no overwrite;
26. templates autoescape;
27. headers de seguridad;
28. cache-control en endpoints sensibles;
29. DB usa agente_forense_app;
30. DB host 127.0.0.1;
31. DB port 5433;
32. no SQL directo desde routes según arquitectura/tests revisables;
33. no filesystem real `casos/`;
34. no PhysicalDrive;
35. no EWF;
36. no AXIOM;
37. no Ollama;
38. no OpenClaw.

---

## 33. Datos de prueba

Solo sintéticos.

No usar:

- RUC real;
- NUE real;
- fotos reales;
- petitorio real;
- E01 real.

---

## 34. PostgreSQL

No modificar esquema salvo necesidad mínima y justificada.

Si hace falta una migración web:

- crear nueva migración;
- no editar silenciosamente `0001_initial_schema.sql` ya aplicado.

Preferir no requerir migración en R02.1.

---

## 35. File Store

No tocar `casos/`.

Usar staging/test root.

La integración definitiva de uploads con estructura real de caso se hará cuando exista RUC/NUE/ESPECIE/DSM implementado operacionalmente.

---

## 36. No realizar

Prohibido:

- OCR;
- petitorio parser;
- identificación automática;
- evidencia real;
- PhysicalDrive;
- ewfacquire;
- ewfverify;
- AXIOM;
- Ollama;
- OpenClaw;
- RAR;
- Word;
- crear caso forense real;
- crear estructura definitiva en `casos/`.

---

## 37. Documentación

Crear:

```text
WEB_ARCHITECTURE.md
```

Debe documentar:

```text
stack real + versiones
comando de inicio
host/port
estructura web
routes
API
error model
upload staging
security headers
logging
PostgreSQL integration
FileStore integration
limitaciones
```

No incluir secrets.

---

## 38. Criterios de aceptación

R02.1 queda COMPLETO si:

- baseline anterior pasa;
- dependencias instaladas y versionadas;
- FastAPI funcional;
- Uvicorn funcional;
- Jinja2 funcional;
- multipart funcional;
- app modular;
- listener solo loopback;
- dashboard funcional;
- health check funcional;
- cases read-only funcional;
- audit read-only funcional;
- system page funcional;
- staging upload sintético funcional;
- streaming/chunking usado;
- SHA-256 verificado;
- límites de upload;
- errores seguros;
- no tracebacks expuestos;
- PostgreSQL accedido solo mediante rol app;
- `casos/` intacto;
- suite completa verde;
- smoke test web realizado;
- listener no expuesto a LAN;
- `WEB_ARCHITECTURE.md` creado.

Estado:

```text
LOCAL_WEB_FOUNDATION_READY
```

Si falla requisito crítico:

```text
LOCAL_WEB_FOUNDATION_BLOCKED
```

---

## 39. Git

Antes de commit:

```text
pytest
git status
```

Confirmar ausencia de:

```text
.env
secrets
runtime/staging files
uploads
casos/
fotos reales
petitorios reales
```

Commit sugerido:

```text
Sprint R02.1: implementa plataforma web localhost
```

---

## 40. Reporte final obligatorio

```text
SPRINT R02.1:
COMPLETADO / INCOMPLETO / BLOCKED

BASELINE:
...

DEPENDENCIES INSTALLED:
FastAPI:
Starlette:
Uvicorn:
Jinja2:
python-multipart:
Pydantic:
httpx:

TESTS BEFORE:
...

WEB ARCHITECTURE:
...

HOST:
...

PORT:
...

LISTENER VERIFIED:
...

DASHBOARD:
...

HEALTH:
...

CASES:
...

AUDIT:
...

SYSTEM:
...

UPLOAD STAGING:
...

MAX UPLOAD:
...

HASHING:
...

ERROR MODEL:
...

REQUEST ID:
...

SECURITY HEADERS:
...

CACHE POLICY:
...

POSTGRES INTEGRATION:
...

FILES CREATED:
...

FILES MODIFIED:
...

TESTS ADDED:
...

TESTS FINAL:
...

WEB SMOKE TEST:
...

LISTENING ON 0.0.0.0:
NO / SI

LAN EXPOSED:
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

RISKS / LIMITATIONS:
...

STATUS:
LOCAL_WEB_FOUNDATION_READY / LOCAL_WEB_FOUNDATION_BLOCKED
```

---

## 41. Instrucción final

TRAE:

1. lee documentación vigente;
2. ejecuta baseline;
3. instala solo dependencias web justificadas;
4. registra versiones reales;
5. implementa FastAPI modular;
6. fuerza localhost;
7. integra repositories existentes;
8. implementa UI server-rendered;
9. implementa uploads solo sintéticos/staging;
10. agrega tests;
11. realiza smoke test local;
12. verifica listener;
13. revisa Git;
14. entrega reporte final;
15. detente;
16. NO inicies R03.

Comienza ahora.
