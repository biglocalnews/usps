from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import text


@dataclass
class SearchResult:
    gid: int
    kind: str
    name: str
    secondary: str


def _compile_query(q: str) -> str:
    """Compile a postgres search query from a string."""
    return "%" + ("%".join(q.split())) + "%"


async def search_tiger(
    conn: AsyncConnection, q: str, limit: int = 10
) -> list[SearchResult]:
    """Perform a search on the TIGER places db."""
    # Interpret filters on `kind` with a `{kind}:{q}` prefix.
    kind_filter = ""
    kind_part, kind_sep, rest_part = q.partition(":")
    if kind_sep:
        kind_filter = kind_part
        q = rest_part

    kind_clause = "kind = :kind AND" if kind_filter else ""

    # Assemble the query. We rank the results to prefer shorter results. This
    # naturally surfaces the real place/cousub/county/state instead of the
    # nested geometries like tracts and blockgroups.
    stmt = text(
        f"""
        SELECT gid, kind, name, secondary, similarity(:orig, name) as rank
        FROM haystack
        WHERE {kind_clause} search ILIKE :q
        ORDER BY rank DESC
        LIMIT :limit
    """
    )

    # Assemble query parameters
    params = {
        "orig": q,
        "q": _compile_query(q),
        "limit": limit,
    }

    if kind_filter:
        params["kind"] = kind_filter

    results = await conn.execute(stmt, params)

    return [
        SearchResult(gid=gid, kind=kind, name=name, secondary=secondary)
        for gid, kind, name, secondary, _ in results
    ]
