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
