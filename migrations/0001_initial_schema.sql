-- Migration: 0001_initial_schema.sql
-- Target: PostgreSQL 18.6
-- Description: Creates forensic schema and foundational relational tables with constraints and audit tracking.

CREATE SCHEMA IF NOT EXISTS forensic;

-- Set default search_path for session
SET search_path TO forensic, public;

-- Schema version tracking
CREATE TABLE IF NOT EXISTS forensic.schema_migrations (
    version VARCHAR(64) PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 1. Cases Table
CREATE TABLE IF NOT EXISTS forensic.cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ruc VARCHAR(64) UNIQUE,
    status VARCHAR(64) NOT NULL DEFAULT 'NEW',
    requesting_unit VARCHAR(255),
    requesting_rut VARCHAR(64),
    request_type VARCHAR(128),
    case_root TEXT,
    state_version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. NUEs Table
CREATE TABLE IF NOT EXISTS forensic.nues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES forensic.cases(id) ON DELETE RESTRICT,
    nue_number VARCHAR(64) NOT NULL,
    description_from_petition TEXT,
    status VARCHAR(64) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_case_nue UNIQUE (case_id, nue_number)
);

-- 3. Species Table
CREATE TABLE IF NOT EXISTS forensic.species (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nue_id UUID NOT NULL REFERENCES forensic.nues(id) ON DELETE RESTRICT,
    species_number INT NOT NULL,
    label VARCHAR(128) NOT NULL,
    description TEXT,
    storage_relation VARCHAR(64) NOT NULL CHECK (storage_relation IN ('SELF_STORAGE', 'CONTAINED_STORAGE')),
    status VARCHAR(64) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_nue_species UNIQUE (nue_id, species_number)
);

-- 4. DSMs Table
CREATE TABLE IF NOT EXISTS forensic.dsms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    species_id UUID NOT NULL REFERENCES forensic.species(id) ON DELETE RESTRICT,
    dsm_number INT NOT NULL,
    label VARCHAR(128) NOT NULL,
    same_physical_object_as_species BOOLEAN NOT NULL DEFAULT TRUE,
    device_type VARCHAR(64),
    brand VARCHAR(128),
    model VARCHAR(128),
    serial VARCHAR(128),
    capacity_bytes BIGINT CHECK (capacity_bytes IS NULL OR capacity_bytes >= 0),
    status VARCHAR(64) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_species_dsm UNIQUE (species_id, dsm_number)
);

-- 5. Files Table
CREATE TABLE IF NOT EXISTS forensic.files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES forensic.cases(id) ON DELETE RESTRICT,
    nue_id UUID REFERENCES forensic.nues(id) ON DELETE RESTRICT,
    species_id UUID REFERENCES forensic.species(id) ON DELETE RESTRICT,
    dsm_id UUID REFERENCES forensic.dsms(id) ON DELETE RESTRICT,
    file_role VARCHAR(64) NOT NULL CHECK (file_role IN ('PETITION', 'PHOTO', 'E01', 'AXIOM_EXPORT', 'PROCESS_SHEET', 'PORTABLE', 'RAR', 'REPORT', 'LOG', 'METADATA', 'OTHER')),
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    relative_path TEXT NOT NULL,
    mime_type VARCHAR(128) NOT NULL,
    size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0),
    sha256 CHAR(64) NOT NULL,
    integrity_status VARCHAR(32) NOT NULL DEFAULT 'VERIFIED',
    source VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. Documents Table
CREATE TABLE IF NOT EXISTS forensic.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES forensic.files(id) ON DELETE RESTRICT,
    document_type VARCHAR(64) NOT NULL CHECK (document_type IN ('PETITION', 'REPORT', 'OTHER')),
    ocr_status VARCHAR(32) NOT NULL DEFAULT 'NOT_PROCESSED',
    ocr_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 7. Photos Table
CREATE TABLE IF NOT EXISTS forensic.photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES forensic.files(id) ON DELETE RESTRICT,
    photo_type VARCHAR(64) NOT NULL DEFAULT 'GENERAL',
    classification_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 8. Hashes Table
CREATE TABLE IF NOT EXISTS forensic.hashes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES forensic.files(id) ON DELETE RESTRICT,
    case_id UUID REFERENCES forensic.cases(id) ON DELETE RESTRICT,
    dsm_id UUID REFERENCES forensic.dsms(id) ON DELETE RESTRICT,
    algorithm VARCHAR(32) NOT NULL,
    hash_value TEXT NOT NULL,
    source VARCHAR(64) NOT NULL,
    verification_status VARCHAR(32) NOT NULL DEFAULT 'VERIFIED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 9. Tool Versions Table
CREATE TABLE IF NOT EXISTS forensic.tool_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_name VARCHAR(128) NOT NULL,
    tool_version VARCHAR(128) NOT NULL,
    executable_path TEXT,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- 10. Case Events Table
CREATE TABLE IF NOT EXISTS forensic.case_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES forensic.cases(id) ON DELETE RESTRICT,
    event_type VARCHAR(64) NOT NULL,
    previous_state VARCHAR(64),
    new_state VARCHAR(64),
    result VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details JSONB
);

-- 11. Audit Events Table (Append-Only)
CREATE TABLE IF NOT EXISTS forensic.audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    case_id UUID REFERENCES forensic.cases(id) ON DELETE RESTRICT,
    nue_id UUID REFERENCES forensic.nues(id) ON DELETE RESTRICT,
    species_id UUID REFERENCES forensic.species(id) ON DELETE RESTRICT,
    dsm_id UUID REFERENCES forensic.dsms(id) ON DELETE RESTRICT,
    actor VARCHAR(128) NOT NULL,
    module VARCHAR(64) NOT NULL,
    tool VARCHAR(64) NOT NULL,
    tool_version VARCHAR(32) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    action VARCHAR(64) NOT NULL,
    source TEXT,
    destination TEXT,
    previous_state VARCHAR(64),
    new_state VARCHAR(64),
    result VARCHAR(32) NOT NULL,
    exit_code INT,
    error TEXT,
    human_confirmation BOOLEAN NOT NULL DEFAULT FALSE,
    details JSONB
);

-- 12. Human Confirmations Table
CREATE TABLE IF NOT EXISTS forensic.human_confirmations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    confirmation_id VARCHAR(128) UNIQUE NOT NULL,
    case_id UUID NOT NULL REFERENCES forensic.cases(id) ON DELETE RESTRICT,
    requested_action VARCHAR(128) NOT NULL,
    summary TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    operator VARCHAR(128),
    request_id VARCHAR(128),
    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMPTZ
);

-- Grant privileges on forensic schema to agente_forense_app
GRANT USAGE ON SCHEMA forensic TO agente_forense_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA forensic TO agente_forense_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA forensic TO agente_forense_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA forensic GRANT ALL ON TABLES TO agente_forense_app;

-- Record initial migration
INSERT INTO forensic.schema_migrations (version, description)
VALUES ('0001_initial_schema', 'Initial relational schema for Agente Forense')
ON CONFLICT (version) DO NOTHING;
