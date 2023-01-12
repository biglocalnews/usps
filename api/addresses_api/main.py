from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .connection import get_db
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


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/shape")
async def shape(kind: str, gid: int):
    db = get_db()

    async with db.connect() as conn:
        return await fetch_shape(conn, kind, gid)


@app.get("/search")
async def search(q: str, limit: int = 10):
    if limit <= 0 or limit > 50:
        raise HTTPException(400, "limit must be in (0, 50]")

    db = get_db()

    async with db.connect() as conn:
        results = await search_tiger(conn, q, limit=limit)
        return {"results": results}
