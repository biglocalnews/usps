from fastapi import Depends, FastAPI
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncEngine

from .connection import get_db
from .sample import SampleRequest, draw_address_sample
from .search import search_tiger
from .shape import fetch_shape

app = FastAPI()


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


@app.get("/")
async def root():
    """Placeholder route at the root of the API.

    Nothing interesting here, but could be used to check if the server is up.
    """
    return {"status": "ok"}


@app.get("/shape")
async def shape(kind: str, gid: int, db: AsyncEngine = Deps.db):
    """Fetch a geometry for the given shape.

    Args:
        kind - Type of geometry (state, county, etc.). See `search.py` for
        more details about accepted types.
        gid - ID of the geometry

    Returns:
        Shape with geometry as a GeoJSON string. Note that this requires the
        client to decode two levels of JSON -- the response itself, then the
        GeoJSON inside the response.
    """
    async with db.connect() as conn:
        return await fetch_shape(conn, kind, gid)


@app.get("/search")
async def search(q: str, limit: int = 10, db: AsyncEngine = Deps.db):
    """Search the TIGER shape data for the given querty.

    Args:
        q - Query to search for. Automatically compiled into wildcards.
        limit - Number of results to return. Cannot exceed 50.

    Returns:
        JSON with the `results` key containing a list of results. The results
        do not contain geometries; those can be fetched with the `/shape`
        endpoint one at a time.
    """
    if limit <= 0 or limit > 50:
        raise HTTPException(400, "limit must be in (0, 50]")

    async with db.connect() as conn:
        results = await search_tiger(conn, q, limit=limit)
        return {"results": results}


@app.post("/sample")
async def sample(params: SampleRequest, db: AsyncEngine = Deps.db):
    """Generate a random sample of addresses against the request.

    Args:
        params - Sampling parameters

    Returns:
        JSON with a random sample of addresses
    """
    async with db.connect() as conn:
        return await draw_address_sample(conn, params)
