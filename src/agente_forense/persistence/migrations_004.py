"""
Migración 004: Creación de la tabla forensic.dsm_disk_bindings para vincular DSMs con discos físicos.
"""

from sqlalchemy import text

MIGRATION_VERSION = "004_dsm_disk_bindings"
DESCRIPTION = "Crear tabla forensic.dsm_disk_bindings para vinculo DSM ↔ PhysicalDrive"

UP_SQL = """
CREATE TABLE IF NOT EXISTS forensic.dsm_disk_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES forensic.cases(id) ON DELETE RESTRICT,
    dsm_id UUID NOT NULL REFERENCES forensic.dsms(id) ON DELETE RESTRICT,
    disk_number INTEGER NOT NULL,
    physical_drive VARCHAR(255) NOT NULL,
    serial_number VARCHAR(255) NULL,
    unique_id TEXT NULL,
    friendly_name TEXT NULL,
    size_bytes BIGINT NOT NULL,
    bus_type VARCHAR(64) NULL,
    is_read_only BOOLEAN NOT NULL,
    is_system BOOLEAN NOT NULL,
    is_boot BOOLEAN NOT NULL,
    is_offline BOOLEAN NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    confirmed_at TIMESTAMPTZ NULL,
    status VARCHAR(64) NOT NULL DEFAULT 'PROPOSED',
    snapshot_json JSONB NOT NULL,
    request_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

INSERT INTO forensic.schema_migrations (version, description, applied_at)
VALUES ('004_dsm_disk_bindings', 'Crear tabla forensic.dsm_disk_bindings', clock_timestamp())
ON CONFLICT (version) DO NOTHING;
"""

DOWN_SQL = """
DROP TABLE IF EXISTS forensic.dsm_disk_bindings;
DELETE FROM forensic.schema_migrations WHERE version = '004_dsm_disk_bindings';
"""

def apply_migration(engine):
    with engine.connect() as conn:
        conn.execute(text(UP_SQL))
        conn.commit()
