import json

from geojson import Feature, MultiPolygon, Point
from pydantic import BaseModel, validator
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import text


class SampleRequest(BaseModel):
    """Describe how to draw a sample of addresses.

    This includes geographic constraints and statistical ones.
    """

    bounds: MultiPolygon
    n: int

    @validator("n")
    def n_positive(cls, v):
        if v <= 0:
            raise ValueError("n must be positive")
        return v

    @validator("bounds")
    def bounds_non_empty(cls, A):
        if not A:
            raise ValueError("sample must be bounded")
        return A


class AddressSample(BaseModel):
    """Sample of addresses with validation information.

    Sample is returned as GeoJSON features.
    """

    n: int
    addresses: list[Feature]
    validation: list[str]


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
    # TODO optimize query
    stmt = text(
        """
        SELECT
            addr,
            St_AsLatLonText(point, 'D.DDDDDDDDD') pt
        FROM oa
        WHERE St_Contains(St_GeomFromGeoJson(:bounds), St_Transform(oa.point, 4269))
        ORDER BY random()
        LIMIT :n
    """
    )

    res = await conn.execute(
        stmt,
        {
            "n": params.n,
            "bounds": json.dumps(params.bounds),
        },
    )

    sample = AddressSample(n=params.n, addresses=[], validation=[])
    for line in res:
        # TODO parse GeoJSON
        addr, pointtxt = line
        coords = [float(c) for c in pointtxt.split()]
        ft = Feature(geometry=Point(coords), properties={"address": addr})
        sample.addresses.append(ft)

    if len(sample.addresses) != params.n:
        sample.validation.append(
            f"Requested {params.n} items but sample drew {len(sample.addresses)}"
        )

    return sample
