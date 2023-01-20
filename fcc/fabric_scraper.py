import csv
import hashlib
import json
import os
from datetime import datetime
from typing import Generator, Iterable

import click
import geojson
import mapbox_vector_tile
import mercantile
import requests
import tqdm

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
            **{k: v for k, v in feature.properties.items() if k not in filter_props}
        )


def fetch_fabric_tile(tile: mercantile.Tile) -> dict:
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

    response = requests.get(url, headers=headers)
    try:
        decoded = mapbox_vector_tile.decode(response.content)
        data = decoded.get("fabriclocation", {})
        # TODO: may be able to skip the initial decode, or use geojson decoder
        # directly in the mapbox_vector_tile library
        fc = geojson.loads(json.dumps(data))
        return fc
    except Exception as e:
        print("Failed to fetch tile:", e)
        print(response.status_code, response.content)
        raise e


def scrape_tiles(tiles: Iterable[mercantile.Tile], output_dir: str):
    """Scrape a list of tiles into the given output directory.

    Directory is organized as `./{zoom}/{x}/{y}/fabric.csv`

    If a file exists already at that location, then we assume the tile is
    already downloaded and we skip it.
    """
    for tile in tqdm.tqdm(list(tiles)):
        tdir = os.path.join(output_dir, str(tile.z), str(tile.x), str(tile.y))
        os.makedirs(tdir, exist_ok=True)

        tout = os.path.join(tdir, "fabric.csv")
        if os.path.exists(tout):
            continue

        # TODO handle errors
        fc = fetch_fabric_tile(tile)

        writer = None
        with open(tout, "w") as fh:
            for line in parse_fabric(tile, fc):
                # Lazily get CSV writer based on first row
                if not writer:
                    writer = csv.DictWriter(fh, line.keys())
                    writer.writeheader()
                writer.writerow(line)

        sha = hashlib.sha256()
        with open(tout, "rb") as fh:
            for block in iter(lambda: fh.read(4096), b""):
                sha.update(block)

        with open(os.path.join(tdir, "metadata.json"), "w") as fh:
            json.dump(
                {
                    "x": tile.x,
                    "y": tile.y,
                    "z": tile.z,
                    "ts": datetime.now().isoformat(),
                    "sha256": sha.hexdigest(),
                },
                fh,
                indent=2,
            )


def parse_input_coord(coord: str) -> mercantile.LngLat:
    """Parse CLI input coord as `{lat},{lng}` and zoom.

    Args:
        coord - string with a comma-delimited `{lat},{lng}`

    Returns:
        mercantile.LngLat object
    """
    coords = [float(c.strip()) for c in coord.split(",")]
    return mercantile.LngLat(coords[1], coords[0])


@click.command()
@click.option("--ul", type=str)
@click.option("--lr", type=str)
@click.option("--tile_dir", type=str)
@click.option("--zoom", type=int, default=DEFAULT_ZOOM)
def run(*, ul: str, lr: str, tile_dir: str, zoom: int):
    """Scrabe Fabric address data in the given bounds.

    Args:
        ul - Upper left coordinates as "{lat},{lng}"
        lr - Lower right coordinates as "{lat},{lng}"
        tile_dir - Directory where tiles should be stored
        zoom - Zoom level. Probably just leave this as default (15).
    """
    ul_coord = parse_input_coord(ul)
    lr_coord = parse_input_coord(lr)
    all_tiles = mercantile.tiles(
        ul_coord.lng, lr_coord.lat, lr_coord.lng, ul_coord.lat, zoom
    )
    scrape_tiles(all_tiles, tile_dir)


if __name__ == "__main__":
    run()
