<script lang="ts">
  import {ChevronUp, ChevronDown} from 'svelte-heros-v2';
  import {createEventDispatcher} from 'svelte';
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
  import formatcoords from 'formatcoords';
  import {labelForBldgType} from '../lib/api.ts';
  import type {Address, Shape} from '../lib/api.ts';

  const dispatch = createEventDispatcher();

  // Whether table is collapsed or shown.
  export let collapse = false;

  // Current sample.
  export let rows: Address[] = [];

  // Show/hide visibility of table.
  const toggle = () => {
    collapse = !collapse;
  };

  // Hover event on the row.
  const hover = (row) => {
    dispatch('hover', row);
  };
</script>

<div class="{collapse ? 'max-h-24' : 'max-h-72'} transition-[max-height]">
  <Tabs
    contentClass="bg-gray-50 rounded-lg dark:bg-gray-800"
    activeClasses="p-4 text-blue-600 bg-white rounded-t-lg dark:bg-gray-800 dark:text-blue-500"
  >
    <TabItem open on:click={toggle}>
      <div slot="title" class="flex items-center gap-2">
        {#if collapse}
          <ChevronUp size="16" /> <span>Show Data</span>
        {:else}
          <ChevronDown size="16" /> <span>Hide Data</span>
        {/if}
      </div>
      <Table hoverable>
        <TableHead>
          <TableHeadCell>Address</TableHeadCell>
          <TableHeadCell>Building Type</TableHeadCell>
          <TableHeadCell>Unit Count</TableHeadCell>
          <TableHeadCell>Coordinates</TableHeadCell>
        </TableHead>
        <TableBody>
          {#each rows as row}
            <TableBodyRow on:click={() => hover(row)}>
              <TableBodyCell>{row.properties.addr}</TableBodyCell>
              <TableBodyCell
                >{labelForBldgType(row.properties.type)}</TableBodyCell
              >
              <TableBodyCell>{row.properties.units}</TableBodyCell>
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
