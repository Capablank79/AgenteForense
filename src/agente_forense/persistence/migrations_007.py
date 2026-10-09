"""
Migración 007: Creación de las tablas de persistencia del Oficio Petitorio para PETITORIO P01.
"""

from sqlalchemy import text

MIGRATION_VERSION = "007_petition_persistence"
DESCRIPTION = "Crear tablas petitions, petition_evidence_items, petition_requested_actions, petition_attachments, petition_field_reviews"

UP_SQL = """
CREATE TABLE IF NOT EXISTS forensic.petitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES forensic.files(id) ON DELETE RESTRICT,
    
    document_type VARCHAR(64) NOT NULL DEFAULT 'PETITION',
    petition_number VARCHAR(128) NULL,
    petition_date VARCHAR(64) NULL,
    city VARCHAR(128) NULL,
    log_reference VARCHAR(128) NULL,
    
    ruc VARCHAR(64) NULL,
    crime_context TEXT NULL,
    other_references TEXT NULL,
    
    requesting_unit VARCHAR(255) NULL,
    prosecutor_office VARCHAR(255) NULL,
    prosecutor_name VARCHAR(255) NULL,
    investigator_name VARCHAR(255) NULL,
    investigator_rank VARCHAR(128) NULL,
    contact_details TEXT NULL,
    addressee VARCHAR(255) NULL,
    informed_copies TEXT NULL,
    
    processing_status VARCHAR(64) NOT NULL DEFAULT 'STAGED',
    review_status VARCHAR(64) NOT NULL DEFAULT 'PENDING',
    
    sha256 VARCHAR(64) NOT NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS forensic.petition_evidence_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    petition_id UUID NOT NULL REFERENCES forensic.petitions(id) ON DELETE RESTRICT,
    nue_number VARCHAR(64) NULL,
    quantity INTEGER NULL CONSTRAINT check_petition_evidence_quantity CHECK (quantity IS NULL OR quantity > 0),
    description_original TEXT NULL,
    evidence_type_declared VARCHAR(128) NULL,
    brand_declared VARCHAR(128) NULL,
    model_declared VARCHAR(128) NULL,
    serial_number_declared VARCHAR(128) NULL,
    capacity_declared VARCHAR(128) NULL,
    source_page INTEGER NULL,
    source_text TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS forensic.petition_requested_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    petition_id UUID NOT NULL REFERENCES forensic.petitions(id) ON DELETE RESTRICT,
    action_order INTEGER NOT NULL CONSTRAINT check_petition_action_order CHECK (action_order >= 1),
    source_text TEXT NOT NULL,
    normalized_action TEXT NULL,
    source_page INTEGER NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS forensic.petition_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    petition_id UUID NOT NULL REFERENCES forensic.petitions(id) ON DELETE RESTRICT,
    attachment_type VARCHAR(64) NOT NULL DEFAULT 'ACTA',
    description TEXT NULL,
    reference_number VARCHAR(128) NULL,
    source_page INTEGER NULL,
    physically_received BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

CREATE TABLE IF NOT EXISTS forensic.petition_field_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    petition_id UUID NOT NULL REFERENCES forensic.petitions(id) ON DELETE RESTRICT,
    field_name VARCHAR(128) NOT NULL,
    observed_value TEXT NULL,
    proposed_value TEXT NULL,
    confirmed_value TEXT NULL,
    source_page INTEGER NULL,
    source_excerpt TEXT NULL,
    extraction_method VARCHAR(64) NULL,
    status VARCHAR(64) NOT NULL DEFAULT 'EXTRACTED',
    review_action VARCHAR(64) NULL,
    reviewed_by VARCHAR(128) NULL,
    reviewed_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp()
);

-- Índices operacionales
CREATE INDEX IF NOT EXISTS idx_petitions_ruc ON forensic.petitions(ruc);
CREATE INDEX IF NOT EXISTS idx_petitions_petition_number ON forensic.petitions(petition_number);
CREATE INDEX IF NOT EXISTS idx_petitions_processing_status ON forensic.petitions(processing_status);
CREATE INDEX IF NOT EXISTS idx_petitions_review_status ON forensic.petitions(review_status);
CREATE INDEX IF NOT EXISTS idx_petitions_file_id ON forensic.petitions(file_id);

CREATE INDEX IF NOT EXISTS idx_petition_evidence_petition_id ON forensic.petition_evidence_items(petition_id);
CREATE INDEX IF NOT EXISTS idx_petition_evidence_nue ON forensic.petition_evidence_items(nue_number);

CREATE INDEX IF NOT EXISTS idx_petition_actions_petition_id ON forensic.petition_requested_actions(petition_id);

CREATE INDEX IF NOT EXISTS idx_petition_attachments_petition_id ON forensic.petition_attachments(petition_id);

CREATE INDEX IF NOT EXISTS idx_petition_reviews_petition_id ON forensic.petition_field_reviews(petition_id);
CREATE INDEX IF NOT EXISTS idx_petition_reviews_field_name ON forensic.petition_field_reviews(field_name);

INSERT INTO forensic.schema_migrations (version, description, applied_at)
VALUES ('007_petition_persistence', 'Crear tablas petitions, petition_evidence_items, petition_requested_actions, petition_attachments, petition_field_reviews', clock_timestamp())
ON CONFLICT (version) DO NOTHING;
"""

DOWN_SQL = """
DROP TABLE IF EXISTS forensic.petition_field_reviews;
DROP TABLE IF EXISTS forensic.petition_attachments;
DROP TABLE IF EXISTS forensic.petition_requested_actions;
DROP TABLE IF EXISTS forensic.petition_evidence_items;
DROP TABLE IF EXISTS forensic.petitions;
DELETE FROM forensic.schema_migrations WHERE version = '007_petition_persistence';
"""


def apply_migration(engine):
    with engine.connect() as conn:
        conn.execute(text(UP_SQL))
        conn.commit()
