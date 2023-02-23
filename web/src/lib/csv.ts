import type {Address} from './api';

/**
 * Add quotes to a CSV cell.
 */
const quo = (s: string | number | boolean) => {
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
  let csv = 'address,longitude,latitude,statefp,countyfp,tractce,blkgrpce';
  for (let addr of addresses) {
    csv += '\n';
    const row = [
      addr.properties.addr,
      addr.geometry.coordinates[0],
      addr.geometry.coordinates[1],
      addr.properties.statefp,
      addr.properties.countyfp,
      addr.properties.tractce,
      addr.properties.blkgrpce,
    ].map((c) => quo(c));
    csv += row.join(',');
  }
  return new Blob([csv], {
    type: 'text/plain;charset=utf-8',
  });
};
