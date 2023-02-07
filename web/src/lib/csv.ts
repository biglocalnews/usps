import type {Address} from './api';

/**
 * Add quotes to a CSV cell.
 */
const quo = (s: string | number) => {
  let str = `${s}`.replace(/"/g, '""');
  const needsQuo = /["\n,]/.test(str);
  if (needsQuo) {
    return `"${str}"`;
  }
  return s;
};

/**
 * Convert address feature list to a CSV.
 */
export const addressListToCsv = (addresses: Address[]) => {
  let csv = 'address,longitude,latitude';
  for (let addr of addresses) {
    csv += '\n';
    const row = [
      addr.properties.address,
      addr.geometry.coordinates[1],
      addr.geometry.coordinates[0],
    ].map((c) => quo(c));
    csv += row.join(',');
  }
  return new Blob([csv], {
    type: 'text/plain;charset=utf-8',
  });
};
