import {env} from '$env/dynamic/public';

const baseUrl = (env.PUBLIC_BASE_URL || '').replace(/\/$/, '');

/**
 * Get the full API URL for the given path.
 *
 * Optionally pass in URL parameters as well.
 */
const url = (path: string, search?: Record<string, any>) => {
  let u = baseUrl;
  if (path[0] !== '/') {
    u += '/';
  }
  u += path;

  if (search) {
    const searchParams = new URLSearchParams();
    for (let k of Object.keys(search)) {
      searchParams.set(k, search[k]);
    }
    u += '?';
    u += searchParams.toString();
  }

  return u;
};

/**
 * Types of shapes that might be used in the app.
 *
 * These are determined by the `/search` feature in the API.
 */
export type ShapeKind =
  | 'state'
  | 'county'
  | 'cousub'
  | 'place'
  | 'tract'
  | 'zcta5';

/**
 * Unit of sample size. Can be either a total count or percentage.
 */
export type SampleSizeUnit = 'total' | 'pct';

/**
 * Reference to a shape, without a geometry included.
 *
 * This type can be passed around cheaply and, when necessary, its underlying
 * geometry can be fetched from the server.
 */
export type ShapePointer = {
  name: string;
  secondary: string;
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
    unit: string;
    number: string;
    street: string;
    city: string;
    county: string;
    state: string;
    zip: string;
    statefp: number;
    countyfp: number;
    tractce: number;
    blkgrpce: number;
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
  unit: SampleSizeUnit,
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
      unit,
    }),
    mode: 'cors',
  });
  return (await res.json()) as ApiSampleResponse;
};
