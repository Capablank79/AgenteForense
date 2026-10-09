"""
Migración 005: Creación de las tablas forensic.acquisition_jobs y forensic.acquisitions para SPRINT R08.1.
"""

from sqlalchemy import text

MIGRATION_VERSION = "005_acquisition_engine"
DESCRIPTION = "Crear tablas forensic.acquisition_jobs y forensic.acquisitions para motor E01 ewfacquire"

UP_SQL = """
CREATE TABLE IF NOT EXISTS forensic.acquisitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES forensic.cases(id) ON DELETE RESTRICT,
    dsm_id UUID NOT NULL REFERENCES forensic.dsms(id) ON DELETE RESTRICT,
    binding_id UUID NOT NULL REFERENCES forensic.dsm_disk_bindings(id) ON DELETE RESTRICT,
    status VARCHAR(64) NOT NULL DEFAULT 'PREPARED',
    target_basename TEXT NOT NULL,
    target_directory TEXT NOT NULL,
    expected_e01_path TEXT NOT NULL,
    acquisition_json_path TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS forensic.acquisition_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(128) UNIQUE NOT NULL,
    acquisition_id UUID NULL REFERENCES forensic.acquisitions(id) ON DELETE RESTRICT,
    case_id UUID NOT NULL REFERENCES forensic.cases(id) ON DELETE RESTRICT,
    dsm_id UUID NOT NULL REFERENCES forensic.dsms(id) ON DELETE RESTRICT,
    binding_id UUID NOT NULL REFERENCES forensic.dsm_disk_bindings(id) ON DELETE RESTRICT,
    status VARCHAR(64) NOT NULL DEFAULT 'PREPARED',
    pid INTEGER NULL,
    command_json JSONB NOT NULL,
    stdout_path TEXT NOT NULL,
    stderr_path TEXT NOT NULL,
    native_log_path TEXT NULL,
    started_at TIMESTAMPTZ NULL,
    finished_at TIMESTAMPTZ NULL,
    exit_code INTEGER NULL,
    error_code VARCHAR(128) NULL,
    human_confirmation_exact VARCHAR(64) NULL,
    human_confirmed_at TIMESTAMPTZ NULL,
    operator VARCHAR(128) NULL,
    details JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

INSERT INTO forensic.schema_migrations (version, description, applied_at)
VALUES ('005_acquisition_engine', 'Crear tablas acquisition_jobs y acquisitions', clock_timestamp())
ON CONFLICT (version) DO NOTHING;
"""

DOWN_SQL = """
DROP TABLE IF EXISTS forensic.acquisition_jobs;
DROP TABLE IF EXISTS forensic.acquisitions;
DELETE FROM forensic.schema_migrations WHERE version = '005_acquisition_engine';
"""

def apply_migration(engine):
    with engine.connect() as conn:
        conn.execute(text(UP_SQL))
        conn.commit()
