/**
 * Take the value of the first matching key from a list of candidates.
 *
 * Case-insensitive and handles partial matches.
 */
export const getFuzzyFeatureProp = (
  properties: Record<string, string>,
  ...keys: Array<string | RegExp>
) => {
  const propKeys = Object.keys(properties);

  for (let k of keys) {
    const pattern: RegExp = typeof k === 'string' ? new RegExp(k, 'i') : k;
    for (let pk of propKeys) {
      if (pattern.test(pk)) {
        return properties[pk];
      }
    }
  }

  return undefined;
};

/**
 * Cache key for the derived name.
 */
const NAME_KEY = '$$tmpName';

/**
 * Try to get a reasonable name for the feature from the given properties.
 */
export const getFeatureName = (
  properties: Record<string, string>,
  fallback?: string,
) => {
  if (properties.hasOwnProperty(NAME_KEY)) {
    return properties[NAME_KEY];
  }

  const name = getFuzzyFeatureProp(properties, 'name', 'id') || fallback || '';
  if (name) {
    properties[NAME_KEY] = name;
  }
  return name;
};
