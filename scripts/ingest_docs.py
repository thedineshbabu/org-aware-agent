"""
Document ingestion CLI — Phase 2.
Usage:
  python ingest_docs.py --source-type pdf --path ./docs/policy.pdf --acl-roles employee,developer
  python ingest_docs.py --source-type confluence --url https://yourorg.atlassian.net/wiki/... --acl-roles employee
"""
import asyncio

try:
    import click
except ImportError:
    raise SystemExit("Install click: pip install click")


@click.command()
@click.option("--source-type", type=click.Choice(["pdf", "docx", "md", "confluence", "html"]), required=True)
@click.option("--path", default=None, help="Local file path")
@click.option("--url", default=None, help="Remote URL (Confluence, HTML)")
@click.option("--acl-roles", default="employee", help="Comma-separated roles that can access this document")
@click.option("--acl-users", default="", help="Comma-separated user IDs with explicit access")
@click.option("--doc-name", default=None, help="Override document display name")
@click.option("--section", default="", help="Section label")
def main(source_type: str, path: str | None, url: str | None, acl_roles: str, acl_users: str, doc_name: str | None, section: str):
    """Ingest a document into the pgvector store."""
    if not path and not url:
        raise click.UsageError("Provide either --path or --url")

    roles = [r.strip() for r in acl_roles.split(",") if r.strip()]
    users = [u.strip() for u in acl_users.split(",") if u.strip()]

    asyncio.run(_ingest(source_type, path, url, roles, users, doc_name, section))


async def _ingest(source_type, path, url, acl_roles, acl_users, doc_name, section):
    # Phase 2 implementation: import rag.ingestion and call ingest_document()
    click.echo(f"[Phase 2] Ingestion not yet implemented — will embed chunks and upsert into document_chunks (pgvector)")
    click.echo(f"  source_type={source_type}, path={path}, url={url}")
    click.echo(f"  acl_roles={acl_roles}, acl_users={acl_users}")


if __name__ == "__main__":
    main()
