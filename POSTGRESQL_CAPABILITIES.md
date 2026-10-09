# POSTGRESQL CAPABILITIES & PERSISTENCE ARCHITECTURE DESIGN
# Project: AGENTE FORENSE
# Sprint: SPRINT_R01 — Real PostgreSQL Investigation & Persistence Design

---

## 1. POSTGRESQL INSTALLED ENVIRONMENT

- **POSTGRESQL_VERSION**: 18.6 (Primary Active Server) / 14.0 (AccessData Secondary Instance)
- **PSQL_VERSION**: 18.6 (`C:\Program Files\PostgreSQL\18\bin\psql.exe`)
- **INSTALLATION_PATH**: `C:\Program Files\PostgreSQL\18` (Data: `C:\Program Files\PostgreSQL\18\data`)
- **SERVICE_NAME**: `postgresql-x64-18`
- **SERVICE_STATUS**: `Running` (StartMode: Auto)
- **SERVER_PORT**: `5433` (PostgreSQL 18.6 listen port; Port 5432 is used by legacy AccessData PostgreSQL 14.0)
- **LISTEN_ADDRESSES**: `*` (Listens on IPv4 `0.0.0.0:5433` and IPv6 `[::]:5433`)
- **AUTH_METHOD**: `scram-sha-256` (Configured in `pg_hba.conf` for IPv4 `127.0.0.1/32`, IPv6 `::1/128` and local socket)
- **DATABASES_OBSERVED**: Native server instance running. Access to custom DBs pending dedicated application role creation in Sprint R01.1.
- **ROLE_STRATEGY**: Create a non-superuser application role `agente_forense_app` with least-privilege access restricted strictly to the `agente_forense_db` database in Sprint R01.1. No administrative/superuser execution for runtime application services.

---

## 2. ENCODING, LOCALE & TIMEZONE

- **SERVER_ENCODING**: `UTF-8` (Standard PostgreSQL UTF-8 encoding verified)
- **CLIENT_ENCODING**: `UTF-8` (Recommended for Python/psycopg drivers to ensure full support for Spanish accents, special characters, and OCR text)
- **COLLATION**: `Spanish_Chile.1252` / `en_US.UTF-8` compatible (Fully compatible with proper names, Spanish legal text, and Windows file paths)
- **TIMEZONE**: `America/Santiago` (Configured in `postgresql.conf`). All audit logs and forensic database timestamps MUST be stored using `TIMESTAMP WITH TIME ZONE` (`timestamptz`) in UTC, while UI presentation layers render in local timezone `America/Santiago`.

---

## 3. EXTENSIONS & DRIVERS

- **EXTENSIONS_AVAILABLE**: 
  - `pgcrypto`: Available (`pgcrypto--1.3.sql`, `pgcrypto.control`)
  - `uuid-ossp`: Available (`uuid-ossp--1.1.sql`, `uuid-ossp.control`)
  - `pgvector`: ABSENT (Not installed in share/extension or lib). 
  *Note: Vector capabilities for future RAG (Sprint R12) will use file-based vector indices (e.g., ChromaDB / FAISS) or dedicated local vector storage.*

- **PYTHON_DRIVER_STATUS**:
  - Python Environment: `3.10.11` (`C:\Program Files\Python310\python.exe`)
  - `psycopg` (v3): `NOT_INSTALLED`
  - `psycopg2`: `NOT_INSTALLED`
  - `asyncpg`: `NOT_INSTALLED`
  - `sqlalchemy`: `2.0.49` (`INSTALLED`)
  - **RECOMMENDATION**: Install `psycopg[binary]` or `psycopg2-binary` in Sprint R01.1 as part of the implementation requirements.

---

## 4. BACKUP & RECOVERY TOOLS

- **PG_DUMP_STATUS**: Available (`C:\Program Files\PostgreSQL\18\bin\pg_dump.exe`, Version 18.6)
- **PG_RESTORE_STATUS**: Available (`C:\Program Files\PostgreSQL\18\bin\pg_restore.exe`, Version 18.6)

---

## 5. PERSISTENCE CONTRACT & FILE STORE DESIGN

### 5.1 Storage Architecture
The Agente Forense persistence layer strictly segregates structured operational memory from heavy forensic binary objects:
1. **PostgreSQL 18.6 (Port 5433)**: Global structured memory, case metadata, relational hierarchy, workflow state engine, hashes, audit trail, and tool execution logs.
2. **File Store (`J:\AgenteForense\AgenteForense\casos`)**: Physical store for documents (petitorios), photos, XLSX process sheets, logs, DOCX reports, Portable Cases, and RAR archives.
3. **E01 Evidence Root (`ADQUISICION`)**: E01 forensic images reside inside `<CASE_ROOT>\ADQUISICION\NUE_<nue>\NUE_<nue>_ESPECIE<n>\NUE_<nue>_ESPECIE<n>_DSM<m>\`. PostgreSQL stores only non-volatile file references, sizes, cryptographic hashes, acquisition metadata, and verification statuses.
4. **`case.json`**: Individual case snapshot file, maintaining local portability and offline inspection capability.

### 5.2 Files Table Logical Contract (`files`)
```sql
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL,
    file_role VARCHAR(64) NOT NULL, -- e.g. PETITORIO, FOTO_EVIDENCIA, PROCESS_SHEET, PORTABLE_CASE_ZIP, REPORT_DOCX
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    relative_path TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    sha256 CHAR(64) NOT NULL,
    mime_type VARCHAR(128) NOT NULL,
    source VARCHAR(64) NOT NULL, -- HUMAN_UPLOAD, AUTOMATED_GENERATION, AXIOM_EXPORT
    integrity_status VARCHAR(32) NOT NULL DEFAULT 'VERIFIED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 5.3 Relational Domain Model (RUC → NUE → ESPECIE → DSM)
```text
RUC (cases)
 └── NUE (nues) [1 RUC -> N NUE]
      └── ESPECIE (species) [1 NUE -> N ESPECIE]
           └── DSM (dsms) [1 ESPECIE -> N DSM]
```
- Supports both `SELF_STORAGE` and `CONTAINED_STORAGE` flags on `species` and `dsms`.
- Links to documents, photos, acquisition jobs, AXIOM jobs, results, and reports via foreign keys to `cases`, `nues`, `species`, and `dsms`.

### 5.4 Audit Model (`audit_events`)
Append-only immutable audit log table:
```sql
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    case_id UUID,
    nue_id UUID,
    species_id UUID,
    dsm_id UUID,
    actor VARCHAR(128) NOT NULL, -- e.g., SYSTEM, OPERATOR_HUMAN, AGENT_IDENTIFICATION
    module VARCHAR(64) NOT NULL,
    tool VARCHAR(64) NOT NULL,
    tool_version VARCHAR(32) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    action VARCHAR(64) NOT NULL,
    source TEXT,
    destination TEXT,
    previous_state VARCHAR(64),
    new_state VARCHAR(64),
    result VARCHAR(32) NOT NULL, -- SUCCESS, FAILED, ABORTED
    exit_code INT,
    error TEXT,
    details JSONB,
    human_confirmation BOOLEAN NOT NULL DEFAULT FALSE
);
```

---

## 6. CREDENTIAL & SECURITY STRATEGY

- **No Passwords in Git/Code**: Credentials will NEVER be stored in `.py`, `.md`, `case.json`, or Git commits.
- **Environment Configuration**: Authentication details (`PGHOST=localhost`, `PGPORT=5433`, `PGUSER=agente_forense_app`, `PGPASSWORD=...`, `PGDATABASE=agente_forense_db`) will be injected via local environment variables or secured local config (`.env` added to `.gitignore`).
- **Least Privilege**: Application will connect using a dedicated non-superuser role `agente_forense_app`. Superuser `postgres` will only be used for database initialization in Sprint R01.1.

---

## 7. BACKUP & RECOVERY RECOMMENDATION

- **Database Backup**: Automated periodic `pg_dump -Fc` dumps of `agente_forense_db` saved to `<BACKUP_ROOT>`.
- **File Store Backup**: Synchronized incremental backup of `casos/` folder.
- **Dual Rebuilding Guarantee**: The system must be capable of reconstructing the PostgreSQL database state from existing `case.json` files if PostgreSQL database failure occurs.

---

## 8. RISKS & BLOCKERS

- **RISKS**:
  1. Listening on `*` (Port 5433): PostgreSQL listens on all network interfaces. Application connections should be restricted to `127.0.0.1` / `localhost` in connection strings.
  2. Multi-instance environment: Presence of legacy AccessData PostgreSQL 14.0 on Port 5432 requires explicitly setting `PGPORT=5433` in configuration.
- **BLOCKERS**: None. PostgreSQL 18.6 is installed, running, accessible on Port 5433, and fully capable of serving as the persistence foundation for Agente Forense.

---

## 9. IMPLEMENTATION RECOMMENDATION FOR SPRINT R01.1

1. In Sprint R01.1, create the database `agente_forense_db` and dedicated non-superuser role `agente_forense_app` on PostgreSQL 18.6 (Port 5433).
2. Install `psycopg[binary]` driver in Python 3.10.11 environment.
3. Apply migration scripts to set up the relational schema (`cases`, `nues`, `species`, `dsms`, `files`, `audit_events`, etc.).
4. Implement sync layer between PostgreSQL and `case.json`.

---

**FINAL STATUS**:
```text
POSTGRES_CAPABILITIES_VERIFIED
```
