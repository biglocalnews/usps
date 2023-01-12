/**
 * API url.
 */
const BASE_URL = 'http://localhost:8000';

/**
 * Get the full API URL for the given path.
 *
 * Optionally pass in URL parameters as well.
 */
const url = (path: string, search?: Record<string, any>) => {
  const q = search ? `?${new URLSearchParams(search).toString()}` : '';
  return `${BASE_URL}${path}${q}`;
};

/**
 * Types of shapes that might be used in the app.
 *
 * These are determined by the `/search` feature in the API.
 */
export type ShapeKind = 'state' | 'county' | 'cousub';

/**
 * Reference to a shape, without a geometry included.
 *
 * This type can be passed around cheaply and, when necessary, its underlying
 * geometry can be fetched from the server.
 */
export type ShapePointer = {
  name: string;
  gid: number;
  kind: ShapeKind;
};

/**
 * Description of a shape with geometry included.
 */
export type Shape = ShapePointer & {
  geom: GeoJSON.MultiPolygon;
};

/**
 * Geometry as returned by the server.
 *
 * This includes the pointer information (gid, kind) for book-keeping, but
 * does not include the human-readable name. The name can be supplied on the
 * client side as necessary -- see the `Shape` type and `fetchShape` function.
 */
export type ApiShapeResponse = Readonly<{
  gid: number;
  kind: ShapeKind;
  geom: string;
}>;

/**
 * List of search results returned by the server.
 */
export type ApiSearchResponse = Readonly<{
  results: ShapePointer[];
}>;

/**
 * Fetch a geometry from the server.
 *
 * This function returns a copy of the input with the geometry attached.
 */
export const fetchShape = async (d: ShapePointer): Promise<Shape> => {
  const res = await fetch(url('/shape', {kind: d.kind, gid: d.gid}));
  const data = (await res.json()) as ApiShapeResponse;
  // Parse the inner geometry, which in practice will always be a multipolygon.
  const geom = JSON.parse(data.geom) as GeoJSON.MultiPolygon;
  return {...d, geom};
};

/**
 * Search shapes for the given token.
 *
 * Returns a list of pointers whose shape geometries can be fetched. See the
 * `fetchShape` function for details.
 */
export const search = async (needle: string): Promise<ShapePointer[]> => {
  const res = await fetch(url('/search', {q: needle}));
  const data = (await res.json()) as ApiSearchResponse;
  return data.results;
};
