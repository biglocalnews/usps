<script lang="ts">
  import {
    Table,
    TableHead,
    TableHeadCell,
    TableBody,
    TableBodyRow,
    TableBodyCell,
    Button,
  } from 'flowbite-svelte';
  import type {Address, Shape} from './api.ts';
  import {addressListToCsv} from './csv.ts';

  // Current boundary (used for generating file name for download).
  export let shape: Shape | null = null;

  // Current sample.
  export let rows: Address[] = [];

  // Default download name (shouldn't ever be used; just in case).
  const defaultName = 'sample-address-data';

  // Browser link to CSV file for download. This is some blob: url with a UUID.
  let csvUrl = '';
  // Human-readable name for the download file, without extension.
  let dataName = defaultName;

  // Generate CSV and give it a reasonable name for downloading.
  $: {
    const csvBlob = addressListToCsv(rows);
    csvUrl = URL.createObjectURL(csvBlob);

    if (shape) {
      dataName = `${shape.properties.name}-${rows.length}-addresses`
        .replace(/\s+/g, '-')
        .replace(/[^\w\d-_]/g, '');
    } else {
      dataName = defaultName;
    }
  }
</script>

<Table>
  <TableHead>
    <TableHeadCell>Address</TableHeadCell>
    <TableHeadCell>Latitude</TableHeadCell>
    <TableHeadCell>Longitude</TableHeadCell>
    <TableHeadCell
      ><a href={csvUrl} download="{dataName}.csv">Download CSV</a
      ></TableHeadCell
    >
  </TableHead>
  <TableBody>
    {#each rows as row}
      <TableBodyRow>
        <TableBodyCell>{row.properties.address}</TableBodyCell>
        <TableBodyCell>{row.geometry.coordinates[1]}</TableBodyCell>
        <TableBodyCell>{row.geometry.coordinates[0]}</TableBodyCell>
        <TableBodyCell />
      </TableBodyRow>
    {/each}
  </TableBody>
</Table>
