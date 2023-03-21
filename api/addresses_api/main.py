from typing import Literal

import geojson
from fastapi import Depends, FastAPI, Query
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine

from .connection import get_db
from .sample import AddressSample, SampleRequest, draw_address_sample
from .search import SearchResults, search_tiger
from .shape import ShapeType, fetch_shape

app = FastAPI(
    title="USPS Address Data API",
    description="API for searching and sampling USPS address data",
    version="0.1.0",
    license_info={
        "name": "MIT License",
        "url": "https://github.com/biglocalnews/usps/blob/main/LICENSE",
    },
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)


app.add_middleware(
    # TODO prod config
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Deps:
    """App dependencies that can be injected."""

    db = Depends(get_db)


@app.get("/", response_model=Literal["hi!"])
async def root() -> Literal["hi!"]:
    """Placeholder route at the root of the API.

    Nothing interesting here, but could be used to check if the server is up.
    """
    return "hi!"


shape_kind = Query(None, description="Type of geometry")
shape_gid = Query(None, description="ID of the geometry in our database")


@app.get("/shape", response_model=geojson.MultiPolygon)
async def shape(
    kind: ShapeType = shape_kind,
    gid: int = shape_gid,
    db: AsyncEngine = Deps.db,
) -> geojson.MultiPolygon:
    """Fetch a geometry for the given shape.

    Returns
        the GeoJSON Feature with shape geometry.
    """
    async with db.connect() as conn:
        return await fetch_shape(conn, kind, gid)


search_q = Query(
    None,
    description="""\
Search string to find shapes in our database.

You can prefix the search with any of the supported `ShapeType` values, such as `state:Vermont`.
""",
)
search_limit = Query(10, description="Maximum number of results to return.")


@app.get("/search", response_model=SearchResults)
async def search(
    q: str = search_q,
    limit: int = search_limit,
    db: AsyncEngine = Deps.db,
) -> SearchResults:
    """Search the TIGER shape data for the given query.

    Returns
        JSON with the `results` key containing a list of results. The results
        do not contain geometries; those can be fetched with the `/shape`
        endpoint one at a time.
    """
    if limit <= 0 or limit > 50:
        raise HTTPException(400, "limit must be in (0, 50]")

    async with db.connect() as conn:
        return await search_tiger(conn, q, limit=limit)


@app.post("/sample", response_model=AddressSample)
async def sample(params: SampleRequest, db: AsyncEngine = Deps.db) -> AddressSample:
    """Generate a random sample of addresses against the request.

    Returns
        JSON with a random sample of addresses, per the given request.
    """
    async with db.connect() as conn:
        return await draw_address_sample(conn, params)
