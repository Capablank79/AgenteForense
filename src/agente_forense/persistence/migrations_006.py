"""
Migración 006: Creación de las tablas de topología e historial de Write-Blockers para SPRINT R08.2.1 REV2.
"""

from sqlalchemy import text

MIGRATION_VERSION = "006_write_blocker_topology"
DESCRIPTION = "Crear tablas write_blockers, write_blocker_observations, write_blocker_attachments, write_blocker_selections"

UP_SQL = """
CREATE TABLE IF NOT EXISTS forensic.write_blockers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blocker_id VARCHAR(128) UNIQUE NOT NULL,
    operator_label VARCHAR(128) NOT NULL,
    manufacturer VARCHAR(128) NULL,
    model VARCHAR(128) NULL,
    serial_number VARCHAR(128) NULL,
    bus VARCHAR(64) NULL,
    pnp_device_id TEXT NULL,
    device_instance_id TEXT NULL,
    vid VARCHAR(32) NULL,
    pid VARCHAR(32) NULL,
    location_path TEXT NULL,
    os_visible BOOLEAN NOT NULL DEFAULT TRUE,
    provenance VARCHAR(128) NOT NULL DEFAULT 'WINDOWS_PNP_CIM_INSPECTION',
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS forensic.write_blocker_observations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blocker_id VARCHAR(128) NOT NULL REFERENCES forensic.write_blockers(blocker_id) ON DELETE RESTRICT,
    operator_label VARCHAR(128) NOT NULL,
    manufacturer VARCHAR(128) NULL,
    model VARCHAR(128) NULL,
    serial_number VARCHAR(128) NULL,
    bus VARCHAR(64) NULL,
    pnp_device_id TEXT NULL,
    device_instance_id TEXT NULL,
    vid VARCHAR(32) NULL,
    pid VARCHAR(32) NULL,
    location_path TEXT NULL,
    os_visible BOOLEAN NOT NULL DEFAULT TRUE,
    provenance VARCHAR(128) NOT NULL DEFAULT 'WINDOWS_PNP_CIM_INSPECTION',
    observed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    details JSONB NULL
);

CREATE TABLE IF NOT EXISTS forensic.write_blocker_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blocker_id VARCHAR(128) NOT NULL REFERENCES forensic.write_blockers(blocker_id) ON DELETE RESTRICT,
    disk_number INTEGER NULL,
    physical_drive VARCHAR(128) NULL,
    disk_friendly_name VARCHAR(255) NULL,
    disk_serial VARCHAR(128) NULL,
    disk_unique_id VARCHAR(255) NULL,
    size_bytes BIGINT NULL,
    is_read_only BOOLEAN NOT NULL DEFAULT TRUE,
    is_system BOOLEAN NOT NULL DEFAULT FALSE,
    is_boot BOOLEAN NOT NULL DEFAULT FALSE,
    relation_status VARCHAR(64) NOT NULL DEFAULT 'CONFIRMED',
    provenance VARCHAR(128) NOT NULL DEFAULT 'PNP_ATTACHMENT_CORRELATION',
    observed_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS forensic.write_blocker_selections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES forensic.cases(id) ON DELETE RESTRICT,
    dsm_id UUID NOT NULL REFERENCES forensic.dsms(id) ON DELETE RESTRICT,
    blocker_id VARCHAR(128) NOT NULL REFERENCES forensic.write_blockers(blocker_id) ON DELETE RESTRICT,
    attachment_id UUID NULL REFERENCES forensic.write_blocker_attachments(id) ON DELETE RESTRICT,
    physical_drive VARCHAR(128) NOT NULL,
    operator VARCHAR(128) NOT NULL DEFAULT 'HUMAN_OPERATOR',
    status VARCHAR(64) NOT NULL DEFAULT 'CONFIRMED',
    selected_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

INSERT INTO forensic.schema_migrations (version, description, applied_at)
VALUES ('006_write_blocker_topology', 'Crear tablas write_blockers, observations, attachments, selections', clock_timestamp())
ON CONFLICT (version) DO NOTHING;
"""

DOWN_SQL = """
DROP TABLE IF EXISTS forensic.write_blocker_selections;
DROP TABLE IF EXISTS forensic.write_blocker_attachments;
DROP TABLE IF EXISTS forensic.write_blocker_observations;
DROP TABLE IF EXISTS forensic.write_blockers;
DELETE FROM forensic.schema_migrations WHERE version = '006_write_blocker_topology';
"""


def apply_migration(engine):
    with engine.connect() as conn:
        conn.execute(text(UP_SQL))
        conn.commit()
