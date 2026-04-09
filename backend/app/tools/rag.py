"""
Hybrid RAG search tool — combines pgvector cosine similarity with PostgreSQL full-text search.

Score fusion formula (Reciprocal Rank Fusion variant):
    final_score = alpha * semantic_rank_score + (1 - alpha) * fts_rank_score

where alpha = settings.rag_hybrid_alpha (default 0.75).
"""
from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.tools import tool
from openai import AsyncOpenAI
from sqlalchemy import text

from app.core.config import get_settings
from app.db.engine import get_session_factory
from app.agent.state import Citation

settings = get_settings()
_openai: AsyncOpenAI | None = None


def _get_openai() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai


async def _embed(query: str) -> list[float]:
    resp = await _get_openai().embeddings.create(
        model="text-embedding-3-small",
        input=query,
    )
    return resp.data[0].embedding


async def _hybrid_search(
    query: str,
    acl_roles: list[str],
    acl_user: str,
    top_k: int,
    alpha: float,
) -> list[dict[str, Any]]:
    acl_filter = """
        (acl_roles && :roles::text[]
         OR :user_id = ANY(acl_users)
         OR array_length(acl_roles, 1) IS NULL)
    """

    # alpha=0 → pure full-text search, no embedding call needed
    if alpha == 0.0:
        sql = text(f"""
            SELECT
                dc.id,
                dc.doc_name,
                dc.section,
                dc.url,
                dc.chunk_text,
                dc.last_updated,
                ts_rank_cd(fts, query) AS hybrid_score
            FROM document_chunks dc,
                 plainto_tsquery('english', :query_text) query
            WHERE {acl_filter}
              AND fts @@ query
            ORDER BY hybrid_score DESC
            LIMIT :top_k
        """)
        params: dict[str, Any] = {
            "query_text": query,
            "roles": acl_roles or ["__none__"],
            "user_id": acl_user,
            "top_k": top_k,
        }
    else:
        embedding = await _embed(query)
        vec_literal = "[" + ",".join(str(x) for x in embedding) + "]"
        sql = text(f"""
            WITH semantic AS (
                SELECT
                    id,
                    1 - (embedding <=> :embedding::vector) AS sem_score
                FROM document_chunks
                WHERE {acl_filter}
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> :embedding::vector
                LIMIT :pool
            ),
            fts AS (
                SELECT
                    id,
                    ts_rank_cd(fts, query) AS fts_score
                FROM document_chunks,
                     plainto_tsquery('english', :query_text) query
                WHERE {acl_filter}
                  AND fts @@ query
                LIMIT :pool
            ),
            combined AS (
                SELECT
                    coalesce(s.id, f.id) AS id,
                    coalesce(s.sem_score, 0) AS sem_score,
                    coalesce(f.fts_score, 0) AS fts_score,
                    :alpha * coalesce(s.sem_score, 0) +
                    (1 - :alpha) * coalesce(f.fts_score, 0) AS hybrid_score
                FROM semantic s
                FULL OUTER JOIN fts f ON s.id = f.id
            )
            SELECT
                dc.id,
                dc.doc_name,
                dc.section,
                dc.url,
                dc.chunk_text,
                dc.last_updated,
                c.hybrid_score
            FROM combined c
            JOIN document_chunks dc ON dc.id = c.id
            ORDER BY c.hybrid_score DESC
            LIMIT :top_k
        """)
        params = {
            "embedding": vec_literal,
            "query_text": query,
            "roles": acl_roles or ["__none__"],
            "user_id": acl_user,
            "alpha": alpha,
            "pool": top_k * 5,
            "top_k": top_k,
        }

    async with get_session_factory()() as session:
        result = await session.execute(sql, params)
        rows = result.mappings().all()

    return [dict(r) for r in rows]


@tool
async def rag_search(query: str, acl_roles: list[str], acl_user: str) -> dict[str, Any]:
    """Search the internal document store using hybrid semantic + keyword search.

    Args:
        query: Natural language question or search phrase.
        acl_roles: List of roles the current user holds (for ACL filtering).
        acl_user: The user's unique ID (for explicit-access ACL filtering).

    Returns:
        A dict with a 'citations' list and a 'context' string ready for the LLM prompt.
    """
    top_k = settings.rag_top_k
    alpha = settings.rag_hybrid_alpha

    try:
        rows = await _hybrid_search(query, acl_roles, acl_user, top_k, alpha)
    except Exception as exc:
        return {
            "citations": [],
            "context": f"Document search is currently unavailable ({type(exc).__name__}). "
                       "Please answer from general knowledge or let the user know you cannot access internal documents right now.",
        }

    citations: list[Citation] = [
        Citation(
            doc_name=r["doc_name"],
            section=r["section"],
            url=r["url"],
            chunk_text=r["chunk_text"],
            last_updated=str(r["last_updated"]),
        )
        for r in rows
    ]

    context = "\n\n---\n\n".join(
        f"[{c.doc_name} / {c.section}]\n{c.chunk_text}" for c in citations
    )

    return {"citations": [c.__dict__ for c in citations], "context": context}
