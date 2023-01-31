import os
import sys

import click
import geojson
from tile_tools import Tile
from tile_tools.cover.tiles import _simplify_tileset
from tile_tools.tilebelt import tile_to_geojson

# A pretty red color.
red = "#F55C47"

# A pretty green color.
green = "#4AA96C"

# Metadata file name.
MD_FILE = "metadata.json"


def check_progress(path: str) -> geojson.FeatureCollection:
    """Create a map of tiles that have been downloaded.

    Args:
        path - Path where tiles have been downloaded.

    Returns:
        GeoJSON FeatureCollection with downloaded tiles.
    """
    tiles = set[Tile]()
    zmax = 0
    print("Inspecting tiles in", path, "(may take a while) ...", file=sys.stderr)

    for dirpath, _, filenames in os.walk(path):
        # If we're not at a leaf, move on.
        if MD_FILE not in filenames:
            continue

        # Parse tile name from directory
        sz, sx, sy = dirpath.lstrip(path).strip(os.path.sep).split(os.path.sep)
        z, x, y = int(sz), int(sx), int(sy)
        tile = (x, y, z)
        if z > zmax:
            zmax = z

        tiles.add(tile)

    print("Simplifying tileset ...", file=sys.stderr)
    simpler_tiles = _simplify_tileset(tiles, (1, zmax))

    print("Generating feature collection ...", file=sys.stderr)
    fts = [
        geojson.Feature(
            geometry=tile_to_geojson(t),
            properties={"fill": green},
        )
        for t in simpler_tiles
    ]

    print("Rendering GeoJSON ...", file=sys.stderr)

    # Generate the feature collection and return it.
    return geojson.FeatureCollection(features=fts)


@click.command()
@click.argument("tilepath")
def run(tilepath: str):
    """Generate GeoJSON FeatureCollection of downloaded tiles.

    Writes results to stdout.

    Args:
        tilepath - Path where tiles are stored.
    """
    fc = check_progress(tilepath)
    print(geojson.dumps(fc))
    print("Done!", file=sys.stderr)


if __name__ == "__main__":
    run()
