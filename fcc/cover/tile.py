"""Partial port of @mapbox/tile-cover:

https://github.com/mapbox/tile-cover/blob/master/index.js
"""
import math
from typing import Optional, Tuple, Union

import geojson

# Constant to convert degrees to radians
d2r = math.pi / 180.0


# Supported geometries. This is all that @mapbox/tile-cover supports.
Geom = Union[
    geojson.Point,
    geojson.MultiPoint,
    geojson.LineString,
    geojson.MultiLineString,
    geojson.Polygon,
    geojson.MultiPolygon,
]

# Tile as (x, y, z)
Tile = Tuple[int, int, int]

# List of (x, y) tile coords
Ring = list[Tuple[int, int]]

# Coordinate as (lng, lat)
Coord = Tuple[float, float]

# Line coordinates
LineCoords = list[Union[Coord, list[float]]]

# Polygon coordinates
PolygonCoords = list[LineCoords]

# Set containing hashed tiles
TileHash = set[int]


def tiles(geom: Geom, zoom: int) -> list[Tile]:
    """Get minimal set of tiles covering a geometry at the zoom level.

    We do not currently implement covering at a range of zoom levels.

    Args:
        geom - geojson Geometry to cover
        zoom - Zoom level to compute tiles for

    Returns:
        List of (x, y, z) tiles
    """
    tiles = list[Tile]()
    tile_hash = TileHash()

    match type(geom):
        case geojson.Point:
            lng, lat = geom.coordinates
            tile_hash = cover_point(lng, lat, zoom)
        case geojson.MultiPoint:
            for point in geom.coordinates:
                phash = cover_point(point[0], point[1], zoom)
                tile_hash |= phash
        case geojson.LineString:
            tile_hash, _ = line_cover(geom.coordinates, zoom)
        case geojson.MultiLineString:
            for line in geom.coordinates:
                lhash, _ = line_cover(line, zoom)
                tile_hash |= lhash
        case geojson.Polygon:
            tile_hash, tiles = polygon_cover(geom.coordinates, zoom)
        case geojson.MultiPolygon:
            for poly in geom.coordinates:
                phash, ptiles = polygon_cover(poly, zoom)
                tile_hash |= phash
                tiles += ptiles
        case _:
            raise NotImplementedError(f"Unsupported geometry type {type(geom)}")

    append_hash_tiles(tile_hash, tiles)
    return tiles


def _id(x: int, y: int, z: int) -> int:
    """Get a hash for the tile.

    The hash is reversible, so the tile can be recovered (see `_from_id`).

    Args:
        x - Tile x coordinate
        y - Tile y coordinate
        z - Tile zoom level

    Returns:
        Integer representing tile
    """
    dim = 2 * (1 << z)
    return ((dim * y + x) * 32) + z


def _from_id(id_: int) -> Tile:
    """Reverse the hash for the tile.

    Args:
        id_ - The tile hash

    Returns:
        Tile as (x, y, z) tuple.
    """
    z = id_ % 32
    dim = 2 * (1 << z)
    xy = (id_ - z) / 32
    x = xy % dim
    y = ((xy - x) / dim) % dim
    return (int(x), int(y), z)


def point_to_tile_fraction(lon: float, lat: float, z: int) -> Tuple[float, float, int]:
    """Convert lng/lat point to a fractional tile coordinate."""
    sin = math.sin(lat * d2r)
    z2 = 2**z
    x = z2 * (lon / 360.0 + 0.5)
    y = z2 * (0.5 - 0.25 * math.log((1 + sin) / (1 - sin)) / math.pi)

    x = x % z2
    if x < 0:
        x += z2

    return (x, y, z)


def point_to_tile(lon: float, lat: float, z: int) -> Tile:
    """Find the tile that covers a given point.

    Args:
        lon - Longitude degrees
        lat - Latitude degrees
        z - Zoom level

    Returns:
        Tile as (x, y, z) integers.
    """
    fx, fy, _ = point_to_tile_fraction(lon, lat, z)
    return (int(math.floor(fx)), int(math.floor(fy)), z)


def cover_point(lon: float, lat: float, z: int) -> TileHash:
    """Get a set containing the tile that covers the given point.

    Args:
        lon - Longitude degrees
        lat - Latitude degrees
        z - Zoom level

    Returns:
        The covered tile. The tile is returned in a set as a hash, for
        consistency with other methods.
    """
    tile = point_to_tile(lon, lat, z)
    return {_id(*tile)}


def append_hash_tiles(tile_hash: TileHash, tile_array: list[Tile]):
    """Decode hashed tiles and merge them into the tile_array.

    Merging happens in place; the function does not return anything.

    Args:
        tile_hash - Set of hashed tiles
        tile_array - List of (x, y, z) tiles.
    """
    for t in tile_hash:
        tile_array.append(_from_id(t))


def polygon_cover(coords: PolygonCoords, zoom: int) -> Tuple[TileHash, list[Tile]]:
    """Get all the tiles covering a polygon.

    Args:
        coords - Polygon coordinates, as a list of lines (which are a list of
        lng/lat coordinates).
        zoom - Current zoom level

    Returns:
        A tuple with a set of tile hashes and a list of covered tiles. The
        hashed tiles and the tile list should be merged eventually.
    """
    tile_hash = TileHash()
    intersections = list[Tuple[int, int]]()
    tile_array = list[Tile]()

    for line in coords:
        line_hash, ring = line_cover(line, zoom)
        tile_hash |= line_hash

        for m in range(len(ring)):
            k = m - 2
            j = m - 1

            ky = ring[k][1]
            y = ring[j][1]
            my = ring[m][1]
            # Check that y is not a local min, not a local max, and is not a
            # duplicate. If all that is true, it is an intersection.
            if (y > ky or y > my) and (y < ky or y < my) and y != my:
                intersections.append(ring[j])

    # Sort the (x,y) tuples by (y,x)
    intersections.sort(key=lambda t: (t[1], t[0]))

    for i in range(0, len(intersections), 2):
        y = intersections[i][1]
        x = intersections[i][0] + 1
        while x < intersections[i + 1][0]:
            if _id(x, y, zoom) not in tile_hash:
                tile_array.append((x, y, zoom))
            x += 1

    return tile_hash, tile_array


def line_cover(line: LineCoords, zoom: int) -> Tuple[TileHash, Ring]:
    """Get a list of tiles covering a line.

    Args:
        line - List of [lng,lat] coordinates.
        zoom - Current zoom level

    Returns:
        Tuple with set of tile hashes and the coordinates ring as a list. The
        ring can be used for computing polygon cover.
    """
    tile_hash = TileHash()
    ring = Ring()
    prev_x: Optional[int] = None
    prev_y: Optional[int] = None

    for i in range(len(line) - 1):
        x0, y0, _ = point_to_tile_fraction(line[i][0], line[i][1], zoom)
        x1, y1, _ = point_to_tile_fraction(line[i + 1][0], line[i + 1][1], zoom)
        dx = x1 - x0
        dy = y1 - y0

        if dx == 0 and dy == 0:
            continue

        sx = 1 if dx > 0 else -1
        sy = 1 if dy > 0 else -1
        x = int(math.floor(x0))
        y = int(math.floor(y0))

        tmax_x = math.inf if not dx else abs(((1 if dx > 0 else 0) + x - x0) / dx)
        tmax_y = math.inf if not dy else abs(((1 if dy > 0 else 0) + y - y0) / dy)
        # Note JavaScript automatically treats 0-div as infinity, so presumably
        # the original authors are OK with this.
        tdx = abs(sx / dx) if dx != 0 else math.inf
        tdy = abs(sy / dy) if dy != 0 else math.inf

        if x != prev_x or y != prev_y:
            tile_hash.add(_id(x, y, zoom))
            ring.append((x, y))
            prev_x = x
            prev_y = y

        while tmax_x < 1 or tmax_y < 1:
            if tmax_x < tmax_y:
                tmax_x += tdx
                x += sx
            else:
                tmax_y += tdy
                y += sy

            tile_hash.add(_id(x, y, zoom))
            if y != prev_y:
                ring.append((x, y))
            prev_x = x
            prev_y = y

    if ring and y == ring[0][1]:
        ring.pop()

    return tile_hash, ring
