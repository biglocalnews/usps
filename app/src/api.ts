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
 * Feature with shape geometry and identifying information.
 */
export type Shape = GeoJSON.Feature<GeoJSON.MultiPolygon, ShapePointer>;

/**
 * Response returned from the API with the shape geometry.
 */
export type ApiShapeResponse = Readonly<GeoJSON.MultiPolygon>;

/**
 * List of search results returned by the server.
 */
export type ApiSearchResponse = Readonly<{
  results: ShapePointer[];
}>;

/**
 * GeoJSON feature representing an address at a lat/lon.
 */
export type Address = GeoJSON.Feature<
  GeoJSON.Point,
  {
    address: string;
  }
>;

/**
 * API response for addresses sample.
 */
export type ApiSampleResponse = Readonly<{
  n: number;
  addresses: Address[];
  validation: string[];
}>;

/**
 * Fetch a geometry from the server.
 *
 * Geometry is returned as GeoJSON feature.
 */
export const fetchShape = async (d: ShapePointer): Promise<Shape> => {
  const res = await fetch(url('/shape', {kind: d.kind, gid: d.gid}));
  const geom = (await res.json()) as ApiShapeResponse;
  return {
    type: 'Feature',
    geometry: geom,
    properties: d,
  };
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

/**
 * Draw a sample from the API.
 */
export const sample = async (
  bounds: GeoJSON.MultiPolygon | ShapePointer,
  n: number,
): Promise<ApiSampleResponse> => {
  const [shapeBounds, customBounds] = bounds.hasOwnProperty('kind')
    ? [bounds, undefined]
    : [undefined, bounds];
  const res = await fetch(url('/sample'), {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      shape_bounds: shapeBounds,
      custom_bounds: customBounds,
      n,
    }),
    mode: 'cors',
  });
  return (await res.json()) as ApiSampleResponse;
};
