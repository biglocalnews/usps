import addressFormatter from '@fragaria/address-formatter';
import type {Address} from './api';

export const formatAddr = (row: Address) => {
  return addressFormatter.format({
    houseNumber: row.properties.number,
    road: row.properties.street,
    city: row.properties.city,
    postcode: row.properties.zip,
    county: row.properties.county,
    state: row.properties.state,
    countryCode: 'US',
  });
};
