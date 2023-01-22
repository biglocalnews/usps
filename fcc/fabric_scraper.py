import asyncio
import csv
import hashlib
import json
import os
import sys
from datetime import datetime
from typing import Generator, Iterable, Optional, Tuple

import click
import cover
import geojson
import httpx
import mapbox_vector_tile
import mercantile
from tqdm.asyncio import tqdm

# Fabric doesn't have a coarser granularity available.
DEFAULT_ZOOM = 15

# FCC Fabric tile server URL template.
PID = "0e56f442-d0b5-4647-b046-e3392946871c"
URL_TPL = "https://broadbandmap.fcc.gov/nbm/map/api/fabric/tile/{pid}/{zoom}/{x}/{y}"

# Params that make us look human
USER_AGENT = """\
Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:108.0) Gecko/20100101 Firefox/108.0\
"""
COOKIE = """\
dtCookie=v_4_srv_1_sn_E63FA4722A06A00116FFD1AAF4C816D7_perc_100000_ol_0_mul_1_app-3A4a4015bed1371d61_1\
"""


def tilecoords2lnglat(
    tile: mercantile.Tile, x: int, y: int, extent: int = 4096
) -> mercantile.LngLat:
    """Convert relative tile coordinates to lng/lat degrees.

    See also:
    https://github.com/tilezen/mapbox-vector-tile#coordinate-transformations-for-encoding

    Args:
        tile - mercantile Tile containing coordinates
        x - horizontal integer pixel offset within tile
        y - vertical integer pixel offset within tile
        extent - pixel space represented by tile (usually 4096)

    Returns:
        mercantile.LngLat object containing degree coordinates
    """
    # Get web mercator bounds of tile
    bounds = mercantile.xy_bounds(tile)
    # Convert pixel offsets to web mercator coordinates
    # The lower left of the tile is (0, 0) and the upper right is (4096, 4096).
    mx = bounds.left + x / float(extent) * (bounds.right - bounds.left)
    my = bounds.bottom + y / float(extent) * (bounds.top - bounds.bottom)
    # Convert spherical mercator to lng/lat.
    return mercantile.lnglat(mx, my)


def parse_fabric(
    tile: mercantile.Tile, fc: geojson.FeatureCollection
) -> Generator[dict, None, None]:
    """Parse Fabric GeoJSON pulled from the given tile.

    Args:
        tile - bounding Tile for data
        fabric - FeatureCollection with Fabric data

    Yields:
        A dict representing a point in the FeatureCollection, with all of its
        properties (aside from uninteresting ones).
    """
    # Properties to exclude from the extraction
    filter_props = {"license"}
    if not fc:
        return
    for feature in fc.features:
        tx, ty = feature.geometry.coordinates
        lnglat = tilecoords2lnglat(tile, tx, ty, extent=fc.extent)
        yield dict(
            id=feature["id"],
            tile_x=tile.x,
            tile_y=tile.y,
            tile_z=tile.z,
            point_x=tx,
            point_y=ty,
            lng=lnglat.lng,
            lat=lnglat.lat,
            **{k: v for k, v in feature.properties.items() if k not in filter_props},
        )


async def fetch_fabric_tile(
    tile: mercantile.Tile,
) -> Tuple[dict, int, Optional[Exception]]:
    """Download Fabric data from the FCC website from the given tile.

    Args:
        tile - desired Tile from Fabric. Note Fabric is only available at zoom
        level 15.

    Returns:
        GeoJSON decoded from the Fabric Tile.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://broadbandmap.fcc.gov/location-summary/fixed",
        "Connection": "keep-alive",
        "Cookie": COOKIE,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers",
    }

    url = URL_TPL.format(pid=PID, zoom=tile.z, x=tile.x, y=tile.y)

    try:
        async with httpx.AsyncClient() as c:
            response = await c.get(url, headers=headers)
    except Exception as e:
        return ({}, 0, e)

    try:
        decoded = mapbox_vector_tile.decode(response.content)
        data = decoded.get("fabriclocation", {})
        # TODO: may be able to skip the initial decode, or use geojson decoder
        # directly in the mapbox_vector_tile library
        fc = geojson.loads(json.dumps(data))
        return (fc, response.status_code, None)
    except Exception as e:
        return ({}, response.status_code, e)


def tile_dir(tile: mercantile.Tile, output_dir: str, create: bool = False) -> str:
    """Get the filesystem directory where tile data should be stored."""
    tdir = os.path.join(output_dir, str(tile.z), str(tile.x), str(tile.y))
    if create:
        os.makedirs(tdir, exist_ok=True)
    return tdir


def fabric_csv_path(tile: mercantile.Tile, output_dir: str, **kwargs) -> str:
    """Get path to CSV for tile fabric data."""
    return os.path.join(tile_dir(tile, output_dir, **kwargs), "fabric.csv")


def metadata_path(tile: mercantile.Tile, output_dir: str, **kwargs) -> str:
    """Get path to tile metadata."""
    return os.path.join(tile_dir(tile, output_dir, **kwargs), "metadata.json")


def hash_file(f: str, blocksize: int = 4096) -> str:
    """Compute hash of file contents.

    Args:
        f - Path to file
        blocksize - Blocks to read at a time from the file

    Returns:
        Hex digest of hash
    """
    sha = hashlib.sha256()
    with open(f, "rb") as fh:
        for block in iter(lambda: fh.read(blocksize), b""):
            sha.update(block)
    return sha.hexdigest()


def needs_update(tile: mercantile.Tile, output_dir: str, strict: bool = False) -> bool:
    """Test whether file should be downloaded again.

    In `strict` mode, we open metadata and look for errors.

    Args:
        tile - Tile to check
        output_dir - Directory containing tile data
        strict - Whether to do a thorough check for data issues

    Returns:
        True if the file should be downloaded again.
    """
    c = fabric_csv_path(tile, output_dir)
    if not os.path.exists(c):
        return True

    m = metadata_path(tile, output_dir)
    if not os.path.exists(m):
        return True

    if strict:
        with open(m, "r") as fh:
            meta = json.load(fh)
            if meta.get("err", None) or meta.get("code") != 200:
                return True
            if meta.get("sha256", "") != hash_file(c):
                return True

    return False


def rm_existing(f: str):
    """Remove file if it exists.

    Args:
        f - Path to file
    """
    try:
        os.remove(f)
    except OSError:
        pass


async def scrape_tile(
    sem: asyncio.Semaphore, tile: mercantile.Tile, output_dir: str, strict: bool = False
):
    await sem.acquire()
    try:
        tout = fabric_csv_path(tile, output_dir, create=True)
        mout = metadata_path(tile, output_dir)

        # Remove file if it exists already
        rm_existing(tout)
        rm_existing(mout)

        fc, status_code, err = await fetch_fabric_tile(tile)
        if err:
            print(f"{tile}\t{status_code}\t{err}", file=sys.stderr)

        # Write CSV
        writer = None
        with open(tout, "w") as fh:
            for line in parse_fabric(tile, fc):
                # Lazily get CSV writer based on first row
                if not writer:
                    writer = csv.DictWriter(fh, line.keys())
                    writer.writeheader()
                writer.writerow(line)

        # Write metadata
        with open(mout, "w") as fh:
            json.dump(
                {
                    "code": status_code,
                    "err": str(err) if err else None,
                    "x": tile.x,
                    "y": tile.y,
                    "z": tile.z,
                    "ts": datetime.now().isoformat(),
                    "sha256": hash_file(tout),
                },
                fh,
                indent=2,
            )
    except Exception as e:
        print(f"Error trying to scrape tile {tile}: {e}", file=sys.stderr)
    finally:
        sem.release()


async def scrape_tiles(
    tiles: Iterable[mercantile.Tile],
    output_dir: str,
    strict: bool = False,
    concurrency: int = 1,
):
    """Scrape a list of tiles into the given output directory.

    Directory is organized as `./{zoom}/{x}/{y}/fabric.csv`

    If a file exists already at that location, then we assume the tile is
    already downloaded and we skip it.
    """
    all_tiles = list(tiles)
    all_n = len(all_tiles)
    filtered_tiles = list[mercantile.Tile]()

    print("Checking previously downloaded files ...")
    async for t in tqdm(all_tiles, unit="files", colour="green"):
        if needs_update(t, output_dir, strict=strict):
            filtered_tiles.append(t)

    # Set progress bar appropriately, when resuming.
    start_at = all_n - len(filtered_tiles)

    if not filtered_tiles:
        print("Nothing to do!")
        return

    print(f"Found {start_at} existing tile(s).")
    print(f"Now downloading {len(filtered_tiles)} new tile(s) ...")

    # Download everything we need, using semaphore to throttle requests.
    sem = asyncio.Semaphore(concurrency)
    tasks = [scrape_tile(sem, t, output_dir, strict=strict) for t in filtered_tiles]
    for f in tqdm.as_completed(
        tasks, total=all_n, initial=start_at, unit="tiles", colour="cyan"
    ):
        await f


def get_tiles(geom: cover.Geom, zoom: int) -> list[mercantile.Tile]:
    """Get a list of mercantile tiles.

    Args:
        geom - GeoJSON geometry
        zoom - Zoom level

    Returns:
        List of mercantile.Tiles covering the geometry.
    """
    return [mercantile.Tile(*t) for t in cover.tiles(geom, zoom)]


@click.command()
@click.option("--tile_dir", "-d", type=str)
@click.option("--feature", "-f", type=str)
@click.option("--zoom", "-z", type=int, default=DEFAULT_ZOOM)
@click.option("--strict", "-s", is_flag=True, default=False)
@click.option("--concurrency", "-n", type=int, default=1)
def run(*, tile_dir: str, feature: str, zoom: int, strict: bool, concurrency: int):
    """Scrabe Fabric address data bounded by the given GeoJSON feature.

    Args:
        tile_dir - Directory where tiles should be stored.
        feature - GeoJSON feature file.
        zoom - Zoom level. Probably just leave this as default (15).
        strict - Whether to check files rigorously and redownload as needed.
        concurrency - Number of requests to make concurrently.
    """
    with open(feature, "r") as fh:
        ft = geojson.load(fh)

    # Parse GeoJSON feature. Can be either a Feature or FeatureCollection.
    all_tiles = list[mercantile.Tile]()
    match type(ft):
        case geojson.FeatureCollection:
            for f in ft.features:
                all_tiles += get_tiles(f.geometry, zoom)
        case geojson.Feature:
            all_tiles += get_tiles(ft.geometry, zoom)
        case _:
            raise NotImplementedError(f"Feature type not supported {type(ft)}")

    asyncio.run(
        scrape_tiles(all_tiles, tile_dir, strict=strict, concurrency=concurrency)
    )


if __name__ == "__main__":
    run()
