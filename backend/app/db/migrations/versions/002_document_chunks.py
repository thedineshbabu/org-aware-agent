"""Add document_chunks table for pgvector hybrid RAG (cosine + full-text)

Revision ID: 002
Revises: 001
Create Date: 2026-04-07
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("doc_name", sa.Text, nullable=False),
        sa.Column("section", sa.Text, nullable=False, server_default=""),
        sa.Column("url", sa.Text, nullable=False, server_default=""),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("acl_roles", postgresql.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("acl_users", postgresql.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # vector(1536) and TSVECTOR can't be expressed via SQLAlchemy Column portably — use raw DDL
    op.execute("ALTER TABLE document_chunks ADD COLUMN embedding vector(1536)")
    op.execute("ALTER TABLE document_chunks ADD COLUMN fts TSVECTOR")

    # Cosine similarity index (ANN)
    op.execute(
        "CREATE INDEX ix_doc_chunks_embedding ON document_chunks "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    # Full-text search index
    op.execute("CREATE INDEX ix_doc_chunks_fts ON document_chunks USING gin (fts)")

    op.create_index("ix_doc_chunks_doc_name", "document_chunks", ["doc_name"])

    # Trigger to keep fts in sync automatically
    op.execute("""
        CREATE OR REPLACE FUNCTION document_chunks_fts_update() RETURNS trigger AS $$
        BEGIN
            NEW.fts := to_tsvector('english',
                coalesce(NEW.doc_name, '') || ' ' ||
                coalesce(NEW.section, '') || ' ' ||
                coalesce(NEW.chunk_text, '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trig_doc_chunks_fts
            BEFORE INSERT OR UPDATE OF doc_name, section, chunk_text
            ON document_chunks
            FOR EACH ROW EXECUTE FUNCTION document_chunks_fts_update()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trig_doc_chunks_fts ON document_chunks")
    op.execute("DROP FUNCTION IF EXISTS document_chunks_fts_update")
    op.drop_table("document_chunks")
