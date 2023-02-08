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
    return "&".join(f"{s}:*" for s in q.lower().split())


async def search_tiger(
    conn: AsyncConnection, q: str, limit: int = 10
) -> list[SearchResult]:
    """Perform a search on the TIGER places db."""
    stmt = text(
        """
        SELECT gid, kind, name, secondary
        FROM haystack
        WHERE tsv @@ to_tsquery(:q)
        LIMIT :limit
    """
    )

    results = await conn.execute(stmt, {"q": _compile_query(q), "limit": limit})

    return [
        SearchResult(gid=gid, kind=kind, name=name, secondary=secondary)
        for gid, kind, name, secondary in results
    ]
