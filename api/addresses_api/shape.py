from typing import Literal

import geojson
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import text

ShapeType = Literal["state", "county", "cousub", "place", "tract", "bg", "zcta5"]


def get_shape_table(kind: ShapeType) -> str:
    """Get the table where a shape can be found."""
    tbl = kind.lower()
    if tbl not in {"state", "county", "cousub", "place", "tract", "bg", "zcta5"}:
        raise ValueError(f"invalid kind {kind}")
    return f"tiger.{tbl}"


async def fetch_shape(
    conn: AsyncConnection, kind: ShapeType, gid: int
) -> geojson.MultiPolygon:
    """Fetch a geometry from the database."""
    tbl = get_shape_table(kind)

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
