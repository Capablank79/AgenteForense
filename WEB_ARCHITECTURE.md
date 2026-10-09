# Arquitectura Web Localhost (Sprint R02.1)

## 1. Stack Tecnológico y Versiones
- **Python**: 3.10.11
- **FastAPI**: 0.142.2
- **Starlette**: 1.7.0
- **Uvicorn**: 0.54.0
- **Jinja2**: 3.1.6
- **python-multipart**: 0.0.32
- **Pydantic**: 2.13.5
- **httpx**: 0.28.1
- **SQLAlchemy**: 2.0.54
- **PostgreSQL**: 18.6 (Puerto 5433, Base `agente_forense_db`, Usuario `agente_forense_app`)

---

## 2. Comando de Inicio
Para iniciar la aplicación web local en modo Uvicorn:

```powershell
.venv\Scripts\python.exe -m uvicorn agente_forense.web.app:app --host 127.0.0.1 --port 8085
```

---

## 3. Host y Puerto
- **Host**: `127.0.0.1` (loopback exclusivo).
- **Puerto**: `8085`.
- **Regla Estricta de Seguridad**: Cualquier intento de binding en `0.0.0.0` o interfaces externamente accesibles (LAN) es rechazado inmediatamente por validación en `WebConfig` lanzando un `SafetyViolationError`.

---

## 4. Estructura del Componente Web
```text
src/agente_forense/web/
├── __init__.py
├── app.py              # Application Factory (create_app) y middlewares de seguridad/logging
├── config.py           # Configuración tipada WebConfig y reglas de binding loopback
├── dependencies.py     # Inyección de dependencias para sesiones SQLAlchemy (DatabaseEngine)
├── errors.py           # Modelo uniforme de errores y exception handler global
├── routes/
│   ├── __init__.py
│   ├── pages.py        # Rutas Jinja2 UI (Dashboard, Casos, Nuevo Caso, Auditoría, Sistema)
│   ├── api_health.py   # Health check (/health) y estado del sistema (/api/system/status)
│   ├── api_cases.py    # API REST de casos (/api/cases, /api/cases/{id}, /api/cases/draft)
│   ├── api_audit.py    # API REST read-only de auditoría (/api/audit)
│   └── api_files.py    # Endpoint de staging de archivos con hashing (/api/files/stage)
└── templates/
    ├── base.html       # Layout base HTML5
    ├── dashboard.html  # Dashboard principal /
    ├── cases.html      # Lista de casos /cases
    ├── case_detail.html# Detalle de caso /cases/{id}
    ├── case_new.html   # Formulario preliminar /cases/new
    ├── audit.html      # Visor de eventos de auditoría /audit
    ├── system.html     # Estado del sistema /system
    └── error.html      # Vista de errores HTML
```

---

## 5. Rutas y Endpoints API

### Rutas UI (Server-Side HTML Rendering via Jinja2)
- `GET /`: Dashboard principal.
- `GET /cases`: Lista de casos registrados.
- `GET /cases/{id}`: Detalle de caso específico.
- `GET /cases/new`: Formulario preliminar de creación de caso (petitorio / fotos).
- `GET /audit`: Visor de eventos de auditoría de solo lectura.
- `GET /system`: Información del sistema y estado de servicios.

### Endpoints API REST (JSON)
- `GET /health`: Estado de salud global (`application`, `database`, `filestore`). Responde HTTP 503 en caso de fallo de BD.
- `GET /api/system/status`: Métricas e información técnica segura sin exposición de credenciales.
- `GET /api/cases`: Listado JSON de casos.
- `GET /api/cases/{id}`: JSON estructurado de un caso por ID.
- `POST /api/cases/draft`: Creación de borrador sintético para testing (sin tocar `casos/`).
- `GET /api/audit`: Registros JSON de eventos de auditoría (máximo 100 eventos, read-only).
- `POST /api/files/stage`: Carga controlada y streaming de archivos a staging temporal.

---

## 6. Modelo de Error Uniforme
Todas las respuestas de error en la API siguen la estructura JSON estandarizada:

```json
{
  "error_code": "NOT_FOUND",
  "message": "Caso no encontrado",
  "request_id": "4b7b2f1e-84b2-4d27-b64d-91b45781a7b4",
  "details_safe": {}
}
```

En caso de excepciones no capturadas, el middleware enmascara los detalles técnicos y responde con un error genérico HTTP 500 y código `INTERNAL_SERVER_ERROR`, registrando el traceback únicamente en el log del servidor y evitando fugas de información.

---

## 7. Upload & File Staging Pipeline
- **Ruta de Staging**: Exclusivamente en `runtime/staging/` (o directorio temporal inyectado), totalmente separado de `casos/`.
- **Procesamiento Streaming**: La recepción de archivos vía multipart (`UploadFile`) utiliza lectura iterativa en chunks de 64 KB (`CHUNK_SIZE`), garantizando bajo uso de memoria RAM.
- **Hashing SHA-256 en vuelo**: Cálculo directo del hash a medida que se escriben los chunks.
- **Límite Configurable**: Tamaño máximo controlado por `max_upload_bytes` (default 100 MB). Si se excede, el archivo parcial es purgado y se responde `HTTP 413 Content Too Large`.
- **Prevención de Overwrite**: Si el archivo ya existe en staging, responde `HTTP 409 Conflict`.
- **Sanitización de Path/Filename**: Validación estricta de nombres y prevención de Path Traversal. Extensiones permitidas en staging: `.txt`, `.pdf`, `.jpg`, `.jpeg`, `.png`.

---

## 8. Headers de Seguridad & No-Cache Policy
Los siguientes cabezales HTTP son inyectados globalmente en todas las respuestas:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`

Adicionalmente, las rutas sensibles de API y vistas de casos/auditoría incluyen:
- `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`

---

## 9. Logging Estructurado
Cada solicitud HTTP genera un registro de trazabilidad que incluye:
- `request_id` (UUID único asignado en middleware)
- `method`
- `path`
- `status_code`
- `duration_ms`

Se prohíbe explícitamente el registro de datos sensibles, credenciales, tokens o contenido completo de archivos subidos.

---

## 10. Integración con PostgreSQL & FileStore
- **Acceso DB**: Realizado mediante la capa de persistencia existente (`DatabaseEngine`) utilizando exclusivamente la cuenta con privilegios mínimos `agente_forense_app`.
- **FileStore**: Se mantiene aislado. El directorio de evidencia real `casos/` no es modificado ni accedido durante operaciones web de staging en el Sprint R02.1.

---

## 11. Limitaciones Conocidas (Sprint R02.1)
1. **Sin Procesamiento Forense Real**: Los formularios y uploads no ejecutan OCR, extracción de metadatos ni parser de petitorios.
2. **Sin CSRF Session-Based**: No existen sesiones de usuario implementadas aún; la protección CSRF basada en cookies/tokens se posterga para sprints con autenticación/sesiones operativas.
3. **Staging Temporal**: Los archivos subidos a staging no se transfieren automáticamente a la estructura forense definitiva.
