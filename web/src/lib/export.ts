import {addressListToCsv} from './csv';
import type {Shape, Address} from './api';

/**
 * Get descriptive name of the export.
 */
export const name = (shape: Shape, data: Address[]) => {
  return `${shape.properties.name}-${data.length}-addresses`
    .replace(/\s+/g, '-')
    .replace(/[^\w\d-_]/g, '');
};

/**
 * Generate a temporary CSV file and return a link to it.
 */
export const csv = (addresses: Address[]) => {
  const csvBlob = addressListToCsv(addresses);
  return URL.createObjectURL(csvBlob);
};
