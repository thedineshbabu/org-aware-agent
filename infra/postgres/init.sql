-- Enable pgvector extension (required before Alembic migrations run)
CREATE EXTENSION IF NOT EXISTS vector;

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
