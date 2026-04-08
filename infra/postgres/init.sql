-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Document chunks table for RAG (Phase 2) — hybrid: cosine similarity + full-text
CREATE TABLE IF NOT EXISTS document_chunks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_name     TEXT NOT NULL,
    section      TEXT NOT NULL DEFAULT '',
    url          TEXT NOT NULL DEFAULT '',
    chunk_text   TEXT NOT NULL,
    embedding    vector(1536),          -- text-embedding-3-small / ada-002 dimension
    fts          TSVECTOR,              -- full-text search vector (auto-maintained by trigger)
    acl_roles    TEXT[] NOT NULL DEFAULT '{}',
    acl_users    TEXT[] NOT NULL DEFAULT '{}',
    last_updated TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Cosine similarity index (ANN via IVFFlat)
CREATE INDEX IF NOT EXISTS ix_doc_chunks_embedding
    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Full-text search index
CREATE INDEX IF NOT EXISTS ix_doc_chunks_fts
    ON document_chunks USING gin (fts);

CREATE INDEX IF NOT EXISTS ix_doc_chunks_doc_name ON document_chunks (doc_name);

-- Trigger: keep fts column in sync with chunk_text, doc_name, section
CREATE OR REPLACE FUNCTION document_chunks_fts_update() RETURNS trigger AS $$
BEGIN
    NEW.fts := to_tsvector('english',
        coalesce(NEW.doc_name, '') || ' ' ||
        coalesce(NEW.section, '') || ' ' ||
        coalesce(NEW.chunk_text, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trig_doc_chunks_fts ON document_chunks;
CREATE TRIGGER trig_doc_chunks_fts
    BEFORE INSERT OR UPDATE OF doc_name, section, chunk_text
    ON document_chunks
    FOR EACH ROW EXECUTE FUNCTION document_chunks_fts_update();

-- Create a read-only role for the agent DB query tool (Phase 3)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'agent_readonly') THEN
        CREATE ROLE agent_readonly WITH LOGIN PASSWORD 'readonly_changeme' NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE orgagent TO agent_readonly;
GRANT USAGE ON SCHEMA public TO agent_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO agent_readonly;
