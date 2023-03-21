from dataclasses import dataclass, field
from typing import Literal, Optional, Tuple, Union

from geojson import Feature, MultiPolygon, Point, dumps
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import text

from .shape import ShapeType, get_shape_table


@dataclass
class ShapePlaceholder:
    """Stand-in for a geometry stored in the database.

    See `./shape.py` for more details.
    """

    kind: ShapeType = field(metadata={"description": "Type of geometry"})
    gid: int = field(metadata={"description": "ID of the geometry in our database"})
    name: Optional[str] = field(
        default=None,
        metadata={
            "description": "Name of the geometry (for presentation only; not required)"
        },
    )


class SampleRequest(BaseModel):
    """Describe how to draw a sample of addresses.

    This includes geographic constraints and statistical ones.

    Either `custom_bounds` or `shape_bounds` must be passed, but not both.
    """

    # Bounds can either be a GeoJSON MultiPolygon, or a reference to a geometry
    # stored in the database. The latter is much faster, but the former allows
    # flexibility (such as drawing a custom geometry in the UI, or uploading
    # a geometry from another GeoJSON file).
    custom_bounds: Optional[MultiPolygon] = Field(
        None, description="Custom GeoJSON MultiPolygon to sample within"
    )
    shape_bounds: Optional[ShapePlaceholder] = Field(
        None, description="Reference to a geometry stored in the database"
    )
    unit: Literal["total", "pct"] = Field(..., description="Unit of `n`")
    n: Union[int, float] = Field(
        ..., description="Number or percentage of addresses to sample"
    )

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

    n: int = Field(..., description="Number of addresses in the sample")
    addresses: list[Feature] = Field(..., description="List of addresses in the sample")
    validation: list[str] = Field(..., description="List of validation messages")


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
        return (
            "SELECT St_Transform(St_GeomFromGeoJson(x), 4269) g FROM (values(:bounds)) s(x)",
            {"bounds": dumps(params.custom_bounds)},
        )


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

    qmax = 50000
    sample_args = {"n": qmax, "p": -1.0}
    match params.unit:
        case "pct":
            sample_args["p"] = float(params.n) / 100.0
        case "total":
            sample_args["n"] = min(qmax, params.n)
        case _:
            raise ValueError(f"invalid sample size unit {params.unit}")

    # Run compiled query
    res = await conn.execute(
        text(
            f"""
            WITH bounds AS (
                {bounds_q}
            )
            SELECT
                s.unit,
                s.number,
                s.street,
                s.city,
                s.district,
                s.region,
                s.postcode,
                s.lon,
                s.lat,
                s.tract_id,
                s.blkgrpce
            FROM bounds b, usps_sample(b.g, :n, :p) s
        """
        ),
        dict(**sample_args, **bounds_args),
    )

    sample = AddressSample(n=params.n, addresses=[], validation=[])
    for line in res:
        (
            unit,
            number,
            street,
            city,
            district,
            region,
            postcode,
            lon,
            lat,
            tract_id,
            blkgrpce,
        ) = line
        ft = Feature(
            geometry=Point([lon, lat]),
            properties={
                "unit": unit,
                "number": number,
                "street": street,
                "city": city,
                "county": district,
                "state": region,
                "zip": postcode,
                "statefp": tract_id[:2],
                "countyfp": tract_id[2:5],
                "tractce": tract_id[5:],
                "blkgrpce": blkgrpce,
            },
        )
        sample.addresses.append(ft)

    if len(sample.addresses) != params.n:
        sample.validation.append(
            f"Requested {params.n} items but sample drew {len(sample.addresses)}"
        )

    return sample
