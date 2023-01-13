from dataclasses import dataclass
from typing import Optional, Tuple

from geojson import Feature, MultiPolygon, Point, dumps
from pydantic import BaseModel, validator
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import text

from .shape import get_shape_table


@dataclass
class ShapePlaceholder:
    """Stand-in for a geometry stored in the database.

    See `./shape.py` for more details.
    """

    name: Optional[str]
    kind: str
    gid: int


class SampleRequest(BaseModel):
    """Describe how to draw a sample of addresses.

    This includes geographic constraints and statistical ones.
    """

    # Bounds can either be a GeoJSON MultiPolygon, or a reference to a geometry
    # stored in the database. The latter is much faster, but the former allows
    # flexibility (such as drawing a custom geometry in the UI, or uploading
    # a geometry from another GeoJSON file).
    custom_bounds: Optional[MultiPolygon]
    shape_bounds: Optional[ShapePlaceholder]
    n: int

    @validator("n")
    def n_positive(cls, v):
        if v <= 0:
            raise ValueError("n must be positive")
        return v

    @validator("custom_bounds", "shape_bounds")
    def bounds_non_empty(cls, value, values, **kwargs):
        if not bool(value) ^ bool(values["custom_bounds"]):
            raise ValueError(
                "must pass either custom_bounds or shape_bounds (not both)"
            )
        return value


class AddressSample(BaseModel):
    """Sample of addresses with validation information.

    Sample is returned as GeoJSON features.
    """

    n: int
    addresses: list[Feature]
    validation: list[str]


def _get_bounds_subquery(params: SampleRequest) -> Tuple[str, dict]:
    """Get the subquery to add a geographic constraint to the query.

    Returns:
        A tuple of the query text and bound parameters.
    """
    if params.shape_bounds:
        tbl = get_shape_table(params.shape_bounds.kind)
        return f"SELECT the_geom g FROM {tbl} WHERE gid = :gid", {
            "gid": params.shape_bounds.gid
        }
    else:
        return "SELECT St_GeomFromGeoJson(x) g FROM (values(:bounds)) s(x)", {
            "bounds": dumps(params.custom_bounds)
        }


async def draw_address_sample(
    conn: AsyncConnection, params: SampleRequest
) -> AddressSample:
    """Draw a sample of addresses from the database.

    The given parameters constrain how the sample is drawn.

    Args:
        conn - Async databaase connection
        params - Constraints to consider when drawing sample

    Returns:
        Sample of address. This contains a list of addresses with their
        geocodes, as well as validation information.
    """
    # TODO optimize query even more. The random() order is fairly slow, there
    # are some other strategies. Large custom geometries are also slow; for
    # the most part queries should be run with geometries already in the DB.
    bounds_q, args = _get_bounds_subquery(params)
    stmt = text(
        f"""
        WITH
        bounds AS (
            {bounds_q}
        ),
        bounded AS (
            SELECT
                oa.addr addr,
                St_AsLatLonText(oa.point, 'D.DDDDDDDDD') p
            FROM oa, bounds
            WHERE St_Contains(bounds.g, oa.point)
        )
        SELECT addr, p
        FROM bounded
        ORDER BY random()
        LIMIT :n
    """
    )

    args["n"] = params.n

    res = await conn.execute(
        stmt,
        args,
    )

    sample = AddressSample(n=params.n, addresses=[], validation=[])
    for line in res:
        addr, pointtxt = line
        lat, lon = [float(c) for c in pointtxt.split()]
        ft = Feature(geometry=Point([lon, lat]), properties={"address": addr})
        sample.addresses.append(ft)

    if len(sample.addresses) != params.n:
        sample.validation.append(
            f"Requested {params.n} items but sample drew {len(sample.addresses)}"
        )

    return sample
