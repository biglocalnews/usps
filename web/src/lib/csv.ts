import type {Address} from './api';
import {formatAddr} from './addr';

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
  let csv =
    'address_full,number,street,city,state,zip,longitude,latitude,statefp,countyfp,tractce,blkgrpce';
  for (let addr of addresses) {
    csv += '\n';
    const row = [
      formatAddr(addr).toUpperCase(),
      // addr.properties.unit,
      addr.properties.number,
      addr.properties.street.toUpperCase(),
      addr.properties.city.toUpperCase(),
      // addr.properties.county.toUpperCase(),
      addr.properties.state.toUpperCase(),
      addr.properties.zip,
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
