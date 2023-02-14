from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

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
    unit: str
    n: Union[int, float]
    types: Optional[List[str]]

    @validator("unit")
    def unit_exists(cls, value):
        value = value.lower()
        if value not in {"total", "pct"}:
            raise ValueError(f"unknown unit {value}")
        return value

    @validator("n")
    def n_positive(cls, v, values):
        if v <= 0:
            raise ValueError("n must be positive")
        if values["unit"] == "pct" and v > 100:
            raise ValueError("can't sample more than 100%")
        return v

    @validator("n")
    def n_whole_count(cls, v, values):
        if values["unit"] == "total" and isinstance(v, float):
            raise ValueError("n must be a whole number")
        return v

    @validator("shape_bounds")
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


def _get_addr_clause(params: SampleRequest) -> Tuple[str, dict]:
    """Get a clause to restrict which samples will be considered.

    Returns:
        A tuple with the filter clause and the bound parameters for it.
    """
    if not params.types:
        return "", {}

    # asyncpg doesn't support WHERE-IN to bind list parameters, so we have to
    # generate a placeholder for each item in the list.
    args = {f"t{i}": v for i, v in enumerate(params.types)}
    placeholders = ",".join(f":{p}" for p in args.keys())

    return f"AND building_type_code IN ({placeholders})", args


def _get_sample_clause(params: SampleRequest) -> Tuple[str, dict]:
    """Get a clause for random sampling based on request.

    Returns:
        A tuple with the clause and the bound parameters it references.
    """
    match params.unit:
        case "pct":
            return "WHERE random() < :n", {"n": params.n / 100.0}
        case "total":
            return "ORDER BY random() LIMIT :n", {"n": params.n}
        case _:
            raise ValueError(f"invalid sample size unit {params.unit}")


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
    bounds_q, bounds_args = _get_bounds_subquery(params)
    addr_q, addr_args = _get_addr_clause(params)
    sample_q, sample_args = _get_sample_clause(params)
    addr_table = "address"
    stmt = text(
        f"""
        WITH
        bounds AS (
            {bounds_q}
        ),
        roughpass AS (
            SELECT statefp, countyfp, tractce
            FROM tract, bounds
            WHERE St_Intersects(the_geom, bounds.g)
        ),
        restricted AS (
            SELECT a.*
            FROM {addr_table} a
            INNER JOIN roughpass b
            ON a.statefp = b.statefp AND a.countyfp = b.countyfp AND a.tractce = b.tractce
        ),
        bounded AS (
            SELECT
                restricted.addr addr,
                St_AsLatLonText(restricted.point, 'D.DDDDDDDDD') p,
                restricted.building_type_code btc,
                restricted.unit_count units,
                restricted.statefp,
                restricted.countyfp,
                restricted.tractce,
                restricted.blkgrpce
            FROM restricted, bounds
            WHERE St_Contains(bounds.g, restricted.point) {addr_q}
        )
        SELECT addr, p, btc, units, statefp, countyfp, tractce, blkgrpce
        FROM bounded
        {sample_q}
    """
    )
    print(stmt)

    # Run compiled query
    res = await conn.execute(
        stmt,
        dict(**bounds_args, **addr_args, **sample_args),
    )

    sample = AddressSample(n=params.n, addresses=[], validation=[])
    for line in res:
        addr, pointtxt, btc, units, statefp, countyfp, tractce, blkgrpce = line
        lat, lon = [float(c) for c in pointtxt.split()]
        ft = Feature(
            geometry=Point([lon, lat]),
            properties={
                "addr": addr,
                "type": btc,
                "units": units,
                "statefp": statefp,
                "countyfp": countyfp,
                "tractce": tractce,
                "blkgrpce": blkgrpce,
            },
        )
        sample.addresses.append(ft)

    if len(sample.addresses) != params.n:
        sample.validation.append(
            f"Requested {params.n} items but sample drew {len(sample.addresses)}"
        )

    return sample
