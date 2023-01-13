import geojson
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import text


def _get_table(kind: str) -> str:
    tbl = kind.lower()
    if tbl not in {"state", "county", "cousub"}:
        raise ValueError(f"invalid kind {kind}")
    return f"tiger.{tbl}"


async def fetch_shape(
    conn: AsyncConnection, kind: str, gid: int
) -> geojson.MultiPolygon:
    """Fetch a geometry from the database."""
    tbl = _get_table(kind)

    stmt = text(
        f"""
        SELECT St_AsGeoJson(the_geom)
        FROM {tbl}
        WHERE gid = :gid
    """
    )

    result = await conn.execute(stmt, {"gid": gid})

    geom = result.fetchone()[0]
    return geojson.loads(geom)
