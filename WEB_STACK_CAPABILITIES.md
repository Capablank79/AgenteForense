# WEB_STACK_CAPABILITIES.md — Evaluación y Definición de Plataforma Web Localhost
**Proyecto**: AGENTE FORENSE
**Sprint**: SPRINT_R02 — Investigación y definición de la plataforma Web Localhost
**Fecha**: 2026-10-07

---

## 1. PYTHON_VERSION
- **Versión de Python**: 3.10.11 (`win32`)
- **Ruta de Ejecutable**: `J:\AgenteForense\AgenteForense\.venv\Scripts\python.exe`

---

## 2. VENV
- **Entorno Virtual**: Presente y activo en `.venv`
- **Pip Version**: 26.2.1 (`J:\AgenteForense\AgenteForense\.venv\lib\site-packages\pip`)

---

## 3. PACKAGES_OBSERVED
Estado real de paquetes observados en `.venv`:

- **Instalados**:
  - `SQLAlchemy`: 2.0.54
  - `psycopg`: 3.3.6
  - `psycopg-binary`: 3.3.6
  - `pytest`: 9.1.1
  - `agente_forense`: 0.1.0 (Proyecto local editable)
  - `setuptools`: 65.5.0
  - `greenlet`: 3.5.6
  - `typing_extensions`: 4.16.0
  - `pluggy`: 1.6.0
  - `exceptiongroup`: 1.3.1
  - `iniconfig`: 2.3.1
  - `packaging`: 26.3
  - `Pygments`: 2.21.0
  - `colorama`: 0.4.6
  - `tomli`: 2.5.0
  - `tzdata`: 2026.5

- **Búsqueda Específica de Frameworks/Servidores Web (NOT_INSTALLED)**:
  - `fastapi`: `NOT_INSTALLED`
  - `starlette`: `NOT_INSTALLED`
  - `uvicorn`: `NOT_INSTALLED`
  - `flask`: `NOT_INSTALLED`
  - `django`: `NOT_INSTALLED`
  - `jinja2`: `NOT_INSTALLED`
  - `werkzeug`: `NOT_INSTALLED`
  - `waitress`: `NOT_INSTALLED`
  - `hypercorn`: `NOT_INSTALLED`
  - `httpx`: `NOT_INSTALLED`
  - `requests`: `NOT_INSTALLED`
  - `python-multipart`: `NOT_INSTALLED`
  - `pydantic`: `NOT_INSTALLED`
  - `pytest-asyncio`: `NOT_INSTALLED`

*Nota*: Ningún framework web o servidor HTTP está instalado actualmente en `.venv`. En R02 no se instala ningún paquete.

---

## 4. BACKEND_CANDIDATES & COMPARISON

### Candidatos Evaluados:
1. **FastAPI + Starlette + Uvicorn**
2. **Flask + Waitress / Werkzeug**
3. **Django**

### Comparativa Técnica:

| Criterio | FastAPI + Starlette + Uvicorn | Flask + Waitress | Django |
| :--- | :--- | :--- | :--- |
| **Soporte Python 3.10 / Windows** | Excelente. Nativo ASGI en Windows. | Excelente. WSGI en Windows. | Excelente. WSGI/ASGI en Windows. |
| **Tipado & Validación** | Pydantic v2 nativo, validación automática de schemas request/response. | Manual o via extensiones (marshmallow). | Formsets / DRF serializers. |
| **Documentación OpenAPI** | Automática e interactiva (/docs, /redoc). | Requiere librerías adicionales (flasgger). | Requiere DRF + drf-spectacular. |
| **Endpoints Async / Sync** | Nativo. Soporta rutas `async def` y `def` concurrentes. | Limitado en WSGI (principalmente sync). | Híbrido, más pesado. |
| **Carga de Archivos (Uploads)** | `UploadFile` (Starlette) con streaming de SpooledTemporaryFile. | `request.files` (Werkzeug FileStorage). | `HttpRequest.FILES`. |
| **Testing** | Excelente con `TestClient` (Starlette/httpx) o Pytest. | Excelente con `app.test_client()`. | `django.test.Client`. |
| **Integración PostgreSQL** | Transparente con SQLAlchemy 2.0 + psycopg3 existente. | Excelente con SQLAlchemy. | ORM propio (duplicaría modelos). |
| **Superficie / Complejidad** | Mínima, modular, altamente performante. | Mínima, monolítica síncrona. | Elevada, incluye ORM propio no deseado. |

---

## 5. SELECTED_BACKEND & RATIONALE
- **Seleccionado**: **FastAPI**
- **Justificación**:
  1. Integración perfecta con **SQLAlchemy 2.0** y **psycopg 3** (ya instalados en el baseline).
  2. Validación estricta con Pydantic v2 para garantizar esquemas de datos seguros en el dominio forense (RUC, NUE, SHA256).
  3. Generación automática de especificación OpenAPI / Swagger UI para auditoría y desarrollo de API sin esfuerzo adicional.
  4. Soporte nativo para endpoints síncronos y asíncronos en Python 3.10.
  5. Desacoplamiento total: no impone ORM ni plantillas rígidas (evita duplicación con la capa de persistencia R01.1).

---

## 6. SELECTED_SERVER & RATIONALE
- **Seleccionado**: **Uvicorn** (ASGI Server)
- **Justificación**:
  1. Servidor ASGI ultra-ligero y estándar para aplicaciones FastAPI/Starlette.
  2. Binding nativo y seguro a loopback (`127.0.0.1`).
  3. Comportamiento probado y estable en Windows 10/11 sin requerir compilación C compleja.

---

## 7. SELECTED_FRONTEND_STRATEGY & RATIONALE
- **Seleccionado**: **Server-rendered HTML + Jinja2 + HTMX** (o HTML estático + Fetch API nativa síncrona/asíncrona)
- **Justificación**:
  1. **Cero complejidad de build**: No requiere Node.js, npm, webpack, Vite ni transpilación JS en la máquina local.
  2. **Operación local mono-puesto**: Renderizado ultra-rápido en servidor web local.
  3. **Interactividad dinámica**: HTMX o Vanilla JS permite actualizar tablas de estado, barras de progreso y petitorios sin recargar la página completa.
  4. **Facilidad de mantenimiento**: Los templates residen directamente en el paquete Python.

---

## 8. LOCALHOST_BINDING
- **Binding Productivo Obligatorio**: `127.0.0.1` (o `localhost`)
- **Prohibiciones por Defecto**: `0.0.0.0` (escucha en todas las interfaces de red) y apertura de puertos en Firewall de Windows quedan estrictamente prohibidos.
- **Comprobación Loopback**: Se verificará que la interfaz sea exclusivamente `127.0.0.1` / `::1`.

---

## 9. PORT_STRATEGY
- **Puerto Seleccionado por Defecto**: `8085` (Rango no privilegiado).
- **Configuración por Entorno**: `AGENTE_FORENSE_WEB_PORT` (configurable vía `.env`).
- **Verificación de Colisión**:
  - `5432` / `5433`: Reservados para PostgreSQL 14.0 y 18.6 (Verificado en uso).
  - `8085`: Verificado desocupado y libre en la estación Windows.

---

## 10. POSTGRES_INTEGRATION
- **Conexión Directa a Capa R01.1**: FastAPI consumirá directamente las sesiones de `SQLAlchemy` a través del patrón `get_db` / `RepositoryFactory`.
- **Credenciales y Rol**: Conexión exclusiva como rol no privilegiado `agente_forense_app` en `127.0.0.1:5433` (DB: `agente_forense_db`, Schema: `forensic`).
- **Regla Estricta**: Las rutas HTTP llamarán a los Application Services / Repositories. Queda prohibido escribir SQL directo o abrir conexiones directas desde plantillas HTML o frontend JS.

---

## 11. UPLOAD_STRATEGY
- **Mecanismo**: Rutas POST multipart multipart/form-data usando streaming a disco staging.
- **Integración con FileStore**:
  1. Recepción en temporal aislado sin cargar archivos gigantes en memoria RAM.
  2. Extracción de nombre original y sanitización anti path traversal vía `agente_forense.storage.paths`.
  3. Cálculo de HASH SHA-256 en bloques de 64KB durante el guardado.
  4. Almacenamiento final en el File Store (`casos/`) gestionado por `FileStore.store_file()`.
  5. Registro de metadatos en la tabla `forensic.files`.

---

## 12. ERROR_MODEL
Formato JSON estandarizado para respuestas HTTP de error (sin revelar stack traces técnicos):

```json
{
  "error_code": "CASE_NOT_FOUND",
  "message": "El caso con el RUC especificado no existe o no se encuentra registrado.",
  "request_id": "req-8f4a12c3b",
  "details_safe": {
    "ruc": "12345678-9"
  }
}
```
- Stack traces y detalles de excepciones internas se escribirán exclusivamente en el log local rotativo del servidor backend.

---

## 13. SESSION_STRATEGY
- **Estrategia Inicial**: Aplicación local mono-operador en laboratorio sin login obligatorio por defecto para la interfaz local `127.0.0.1`.
- **Evolución Futura**: Si se requiere aislamiento de operador, se empleará cookie de sesión HTTP-only firmada localmente (`SecretKey` autogenerada en `.env`).

---

## 14. CSRF_STRATEGY
- Para solicitudes POST/PUT/DELETE basadas en formularios HTML server-rendered, se utilizará un token CSRF almacenado en la sesión local o validación de header `X-Requested-With` / SameSite `Strict` en cookies locales.

---

## 15. LONG_RUNNING_JOB_STRATEGY
- **Desacoplamiento HTTP / Job**: Una petición HTTP POST inicia el trabajo, genera un registro de trabajo/evento en la base de datos PostgreSQL (`job_id`, `state='RUNNING'`) y responde de inmediato con HTTP 202 Accepted.
- **Ejecución**: Los trabajos de adquisición (E01), verificación (EWF), AXIOM o generación de reportes se ejecutan en un worker/thread en segundo plano desacoplado del lifecycle del request HTTP.
- **Persistencia de Estado**: El estado del trabajo persiste en la tabla `audit_events` / `case_events` de PostgreSQL, garantizando que el cierre o recarga del navegador no cancele el proceso.

---

## 16. PROGRESS_UPDATE_STRATEGY
- **Estrategia Inicial**: Polling periódico ligero desde el frontend via JS/HTMX (`GET /api/jobs/{id}/status` cada 2-5 segundos).
- **Alternativa Futura**: SSE (Server-Sent Events) sobre la conexión HTTP en FastAPI para stream continuo de logs de progreso en vivo.

---

## 17. INITIAL_ROUTES
- `/`: Dashboard principal (RUCs activos, estado del sistema).
- `/cases`: Listado general de causas.
- `/cases/new`: Formulario de ingreso de petitorio / fotografías.
- `/cases/{id}`: Ficha detallada del caso (NUEs, Especies, DSMs).
- `/audit`: Visualizador de bitácora de auditoría inmutable.
- `/system`: Estado de salud e infraestructura local.

---

## 18. INITIAL_API
- `GET /health`: Estado del sistema, DB PostgreSQL y FileStore.
- `GET /api/system/status`: Métricas y versiones locales de herramientas.
- `GET /api/cases`: Lista de casos registrados.
- `GET /api/cases/{id}`: Detalle de un caso específico.
- `GET /api/audit`: Eventos de auditoría filtrables.
- `POST /api/cases/draft`: Creación de borrador de caso (RUC/Petitorio).
- `POST /api/files/stage`: Carga staging de archivos documentales.

---

## 19. DEPENDENCIES_REQUIRED_FOR_R02_1
Para la implementación en SPRINT_R02.1 se requerirá la instalación de las siguientes dependencias mínimas en `.venv`:
1. `fastapi` (Framework Web / API)
2. `uvicorn[standard]` (Servidor ASGI)
3. `jinja2` (Motor de plantillas HTML)
4. `python-multipart` (Soporte para carga de archivos multipart/form-data)
5. `pydantic` (Validación de esquemas JSON, usualmente incluido con FastAPI)

---

## 20. SECURITY_NOTES
- Binding estricto a loopback `127.0.0.1`.
- Sanitización de rutas de archivos subidos para prevenir vulnerabilidades de Path Traversal (`..`, `/`, `\`).
- Hashes SHA-256 obligatorios pre y post guardado en File Store.
- Ocultación total de tracebacks y contraseñas en respuestas HTTP.

---

## 21. RISKS
- **Manejo de archivos gigantes**: Cargas de evidencias de gran tamaño deben pasar por streaming directo a disco para evitar desbordamientos de memoria RAM.
- **Puertos**: Debe garantizarse que el puerto `8085` no sea modificado por software de terceros.

---

## 22. BLOCKERS
- **Ninguno**. La estación Windows dispone de Python 3.10.11, PostgreSQL 18.6 corriendo en puerto 5433 y entorno `.venv` listo para la futura fase R02.1.

---

**ESTADO FINAL DE EVALUACIÓN**:
```text
LOCAL_WEB_STACK_VERIFIED
```
