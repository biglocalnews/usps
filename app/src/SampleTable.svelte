<script lang="ts">
  import {
    Table,
    TableHead,
    TableHeadCell,
    TableBody,
    TableBodyRow,
    TableBodyCell,
    Button,
    Tabs,
    TabItem,
  } from 'flowbite-svelte';
  import type {Address, Shape} from './api.ts';
  import formatcoords from 'formatcoords';

  // Whether table is collapsed or shown.
  export let collapse = true;

  // Current sample.
  export let rows: Address[] = [];

  // Show/hide visibility of table.
  const toggle = () => {
    collapse = !collapse;
  };
</script>

<div class="{collapse ? 'max-h-24' : 'max-h-72'} transition-[max-height]">
  <Tabs
    contentClass="bg-gray-50 rounded-lg dark:bg-gray-800"
    activeClasses="p-4 text-blue-600 bg-white rounded-t-lg dark:bg-gray-800 dark:text-blue-500"
  >
    <TabItem open title="{collapse ? 'Show' : 'Hide'} Data" on:click={toggle}>
      <Table>
        <TableHead>
          <TableHeadCell>Address</TableHeadCell>
          <TableHeadCell>Coordinates</TableHeadCell>
        </TableHead>
        <TableBody>
          {#each rows as row}
            <TableBodyRow>
              <TableBodyCell>{row.properties.address}</TableBodyCell>
              <TableBodyCell
                >{formatcoords(
                  row.geometry.coordinates,
                  true,
                ).format()}</TableBodyCell
              >
            </TableBodyRow>
          {/each}
        </TableBody>
      </Table>
    </TabItem>
  </Tabs>
</div>
