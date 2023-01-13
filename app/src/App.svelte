<script lang="ts">
  import {
    Heading,
    Button,
    Input,
    Badge,
    Spinner,
    CloseButton,
    Navbar,
    NavBrand,
    NavUl,
    NavLi,
  } from 'flowbite-svelte';
  import Search from './Search.svelte';
  import AddrMap from './AddrMap.svelte';
  import SampleTable from './SampleTable.svelte';
  import * as api from './api.ts';
  import type {Address, Shape} from './api.ts';

  let sample: Address[] = [];
  let loading = false;
  let sampleSize = 20;
  let selectedShape: Shape | null = null;

  // Load GeoJSON representing the selected item.
  const fetchShape = async (e) => {
    sample = [];
    selectedShape = null;
    selectedShape = await api.fetchShape(e.detail);
  };

  // Load sample data in the current boundary.
  const fetchSample = async (e) => {
    loading = true;
    sample = [];
    const sampleRes = await api.sample(selectedShape.geometry, sampleSize);

    sample = sampleRes.addresses;
    loading = false;
  };

  // Clear current boundary / sample.
  const clearSelection = async (e) => {
    if (loading) {
      return;
    }
    sample = [];
    selectedShape = null;
  };
</script>

<main class="flex h-screen w-screen overflow-hidden">
  <AddrMap bounds={selectedShape} addresses={sample} />
  {#if selectedShape}
    <Navbar navClass="fixed w-full">
      <NavBrand>Addresses</NavBrand>
      <NavUl
        ulClass="flex flex-col p-2 mt-1 md:flex-row md:space-x-8 md:mt-0 md:text-sm md:font-medium items-center"
      >
        <NavLi>
          <Badge large>
            {selectedShape.properties.name}
            <CloseButton
              size="sm"
              class="ml-3 -mr-1.5"
              disabled={loading}
              on:click={clearSelection}
            />
          </Badge>
        </NavLi>
        <NavLi>
          <Input type="number" id="n" bind:value={sampleSize} />
        </NavLi>
        <NavLi>
          <Button
            gradient
            disabled={loading}
            size="sm"
            color="purpleToPink"
            on:click={fetchSample}
          >
            Sample
            {#if loading}
              <Spinner class="ml-3" size="4" />
            {/if}
          </Button>
        </NavLi>
      </NavUl>
    </Navbar>
  {/if}
  {#if !selectedShape}
    <div class="container m-auto p-16 z-10">
      <header class="py-8">
        <Heading>US Address Sampler</Heading>
      </header>
      <div>
        <Search on:select={fetchShape} />
      </div>
    </div>
  {/if}
  {#if sample.length}
    <div class="absolute bottom-0 left-0 w-screen max-h-72 z-10">
      <SampleTable rows={sample} shape={selectedShape} />
    </div>
  {/if}
</main>
