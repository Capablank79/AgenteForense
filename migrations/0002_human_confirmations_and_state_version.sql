-- Migration: 0002_human_confirmations_and_state_version.sql
-- Target: PostgreSQL 18.6
-- Description: Adds state_version to forensic.cases for optimistic concurrency control and creates forensic.human_confirmations table.

ALTER TABLE forensic.cases ADD COLUMN IF NOT EXISTS state_version INT NOT NULL DEFAULT 1;

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

INSERT INTO forensic.schema_migrations (version, description)
VALUES ('0002_human_confirmations_and_state_version', 'Adds state_version to cases and human_confirmations table')
ON CONFLICT (version) DO NOTHING;
