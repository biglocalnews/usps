import asyncio
import csv
import ctypes
import os
import pathlib
import sys
from datetime import datetime
from getpass import getpass
from typing import List, Tuple

import click
import orjson as json
from geoalchemy2 import Geometry
from sqlalchemy import Column, ForeignKeyConstraint, Index, PrimaryKeyConstraint
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)
from tqdm.asyncio import tqdm


class Base(DeclarativeBase):
    pass


class FabricTile(Base):
    __tablename__ = "fabric_tile"

    x: Mapped[int] = mapped_column(nullable=False)
    y: Mapped[int] = mapped_column(nullable=False)
    z: Mapped[int] = mapped_column(nullable=False)
    code: Mapped[int] = mapped_column(index=True, nullable=False, default=0)
    error: Mapped[str] = mapped_column(nullable=True)
    ts: Mapped[datetime] = mapped_column(index=True, nullable=True)

    addresses: Mapped[List["FabricAddress"]] = relationship(
        back_populates="tile", cascade="all, delete-orphan"
    )

    __table_args__ = (PrimaryKeyConstraint(x, y, z),)


class FabricAddress(Base):
    __tablename__ = "fabric_address"

    location_id: Mapped[int] = mapped_column(primary_key=True)
    id: Mapped[int] = mapped_column(index=True)
    tx: Mapped[int] = mapped_column(nullable=False)
    ty: Mapped[int] = mapped_column(nullable=False)
    tz: Mapped[int] = mapped_column(nullable=False)
    tile: Mapped["FabricTile"] = relationship(back_populates="addresses")
    sx: Mapped[int] = mapped_column(nullable=False)
    sy: Mapped[int] = mapped_column(nullable=False)
    point = Column(Geometry("Point"), nullable=False)
    unit_count: Mapped[int]
    building_type_code: Mapped[str] = mapped_column(nullable=False)
    addr: Mapped[str] = mapped_column(nullable=False)
    bsl_flag: Mapped[bool] = mapped_column(nullable=False, default=False)

    __table_args__ = (
        Index("f_point_idx", point, postgresql_using="GIST"),
        ForeignKeyConstraint([tx, ty, tz], [FabricTile.x, FabricTile.y, FabricTile.z]),
    )


# Address request metadata.
MD_FILE = "metadata.json"

# Address data file.
AD_FILE = "fabric.csv"

# Errors that occurred while ingesting.
ERROR_LOG = "ingest-errors.log.tsv"


def count_tiles(tile_dir: str) -> int:
    """Count number of tiles in the directory.

    This function depends on the `counttiles.so` C library, which can count
    stuff much, much faster. Even in C the function can only count a ~100k
    tiles per second, so there is a bit of a delay in getting the result for
    sizable tilesets. There are about 15 million tiles in the entire US at
    zoom level 15!

    Args:
        tile_dir - Root tile directory

    Returns:
        Count of tiles.
    """
    libname = pathlib.Path().absolute() / "counttiles" / "counttiles.so"
    c_lib = ctypes.CDLL(str(libname))

    return c_lib.count_tiles(ctypes.c_char_p(tile_dir.encode("utf-8")))


def _parse_tile_coords(dirpath: str) -> Tuple[int, int, int]:
    """Fast function to parse tile coordinates from directory.

    Assumes directory has an `{zoom}/{x}/{y}` component at the end.

    Args:
        dirpath - Directory path

    Returns:
        Parsed (x, y, z) tuple.
    """
    char0 = ord("0")
    yxz = [0, 0, 0]
    n = 1
    ptr = 0

    # Dirpath looks like:
    #  data/tiles/15/1069/10633
    # And we want to parse (z, x, y).
    # We start at the end of the string and work backwards. When we hit a
    # separator, move to the next path component.
    for i in range(len(dirpath) - 1, -1, -1):
        if dirpath[i] == os.path.sep:
            # Catch trailing slash.
            if n == 1 and ptr == 0:
                continue
            # Move on to the next path component.
            n = 1
            ptr += 1
            # Catch terminal condition.
            if ptr > 2 or i == 0:
                break
            continue
        # Parse the next digit and add it to the total sum.
        yxz[ptr] += (ord(dirpath[i]) - char0) * n
        # Increment the exponent.
        n *= 10

    # Return things in the right order.
    y, x, z = yxz
    return x, y, z


async def ingest_tiles(db: AsyncEngine, tile_dir: str, tx_batch: int = 10000):
    """Quickly import tiles from filesystem into Postgres.

    Args:
        db - SqlAlchemy / Postgres Engine.
        tile_dir - Root directory to load tiles from
        tx_batch - Number of tiles to read before committing. The number of
        rows in the addresses table can vary substantially, depending on the
        address density in the tileset.
    """
    print("🏗  Creating database tables if necessary ...")
    async with db.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
    async_session = sessionmaker(db, expire_on_commit=False, class_=AsyncSession)

    print("🧩 Counting tiles. This might take up to a minute ...")
    ntiles = count_tiles(tile_dir)

    print("📦 Ingesting tiles. This can take a very long time!")
    ctr = 0
    with open(ERROR_LOG, "w") as err_fh:
        err_fh.seek(0)
        err_fh.truncate()

        async with async_session() as session:
            with tqdm(range(ntiles), unit="tiles", colour="red") as pbar:
                for dirpath, _, filenames in os.walk(tile_dir):
                    # Quick check to see if we're at a leaf directory. There are never
                    # any files in the higher directories and always 2 in the leaves,
                    # so this check is always very fast and correct.
                    if len(filenames) != 2:
                        continue

                    try:
                        # Load the metadata. We have to do this regardless of whether the
                        # addresses file is empty, since we need to know when the tile was
                        # fetched / whether there was an error.
                        with open(os.path.join(dirpath, MD_FILE), "r") as fh:
                            md = json.loads(fh.read())
                        x, y, z = _parse_tile_coords(dirpath)

                        tile = FabricTile(
                            x=x,
                            y=y,
                            z=z,
                            code=md["code"],
                            error=md["err"],
                            ts=datetime.strptime(md["ts"], "%Y-%m-%dT%H:%M:%S.%f"),
                        )
                        session.add(tile)

                        # Optimize by using stat to avoid opening empty files, of which
                        # there are many, especially up in Alaska.
                        stat = os.stat(os.path.join(dirpath, AD_FILE))
                        if stat.st_size > 0:
                            with open(os.path.join(dirpath, AD_FILE), "r") as fh:
                                rdr = csv.reader(fh)
                                for i, row in enumerate(rdr):
                                    if i == 0:
                                        continue
                                    addr = FabricAddress(
                                        id=int(row[0]),
                                        tx=x,
                                        ty=y,
                                        tz=z,
                                        tile=tile,
                                        sx=int(row[4]),
                                        sy=int(row[5]),
                                        point=f"POINT({float(row[6])} {float(row[7])})",
                                        location_id=int(row[8]),
                                        unit_count=int(row[9]),
                                        building_type_code=row[10],
                                        addr=row[11],
                                        bsl_flag=row[12] == "True",
                                    )
                                    session.add(addr)

                        # Commit the session periodically
                        ctr += 1
                        if ctr >= tx_batch:
                            await session.commit()
                            ctr = 0

                        pbar.update(1)
                    except Exception as e:
                        print(
                            f"❌ Error processing tile {dirpath}: {e}", file=sys.stderr
                        )
                        print(f"{dirpath}\t{e}", file=err_fh)

            # Commit any more pending data before closing the transaction.
            print("🧹 Committing any lingering data ...")
            await session.commit()


@click.command()
@click.option("--tile_dir", "-d", type=str, required=True)
@click.option("--host", "-H", type=str)
@click.option("--port", "-P", type=int, default=5432)
@click.option("--user", "-u", type=str)
@click.option("--password", "-p", is_flag=True, default=False)
@click.option("--database", "-D", type=str, required=True)
def run(
    *,
    tile_dir: str,
    host: str,
    port: int,
    user: str,
    password: bool,
    database: str,
):

    pw = getpass() if password else None
    db_url = URL.create(
        "postgresql+asyncpg",
        username=user,
        password=pw,
        host=host,
        port=port,
        database=database,
    )
    print("📞 Connecting to the database ...")
    engine = create_async_engine(db_url)
    asyncio.run(ingest_tiles(engine, tile_dir))
    print("🤙 Done!")


if __name__ == "__main__":
    run()
