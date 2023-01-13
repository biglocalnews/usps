<script lang="ts">
  import {
    Heading,
    Dropdown,
    DropdownItem,
    Button,
    ButtonGroup,
    Input,
    Badge,
    Spinner,
    CloseButton,
    Navbar,
    NavBrand,
    NavUl,
    NavLi,
    Label,
    Modal,
    SpeedDial,
    SpeedDialButton,
  } from 'flowbite-svelte';
  import Search from './Search.svelte';
  import AddrMap from './AddrMap.svelte';
  import SampleTable from './SampleTable.svelte';
  import Help from './Help.svelte';
  import * as api from './api.ts';
  import * as exportTools from './export.ts';
  import type {Address, Shape, SampleSizeUnit} from './api.ts';

  let sample: Address[] = [];
  let loading = false;
  let sampleSize = 20;
  let selectedShape: Shape | null = null;
  let unit: SampleSizeUnit = 'total';
  let unitMenuOpen = false;
  let csvUrl = '';
  let exportName = '';
  let helpOpen = false;

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
    const sampleRes = await api.sample(
      selectedShape.properties,
      sampleSize,
      unit,
    );

    sample = sampleRes.addresses;
    loading = false;
  };

  // Clear current boundary / sample.
  const clearSelection = (e) => {
    if (loading) {
      return;
    }
    sample = [];
    selectedShape = null;
  };

  // Set sample size unit to new value.
  const setUnit = (u: SampleSizeUnit) => {
    unit = u;
    unitMenuOpen = false;
  };

  // Get a readable label for the sample size unit.
  const labelForUnit = (u: SampleSizeUnit) => {
    switch (u) {
      case 'total':
        return 'total';
      case 'pct':
        return 'percent of';
    }
  };

  // Open the dropdown for the sample size unit.
  const openUnitMenu = () => {
    unitMenuOpen = true;
  };

  $: {
    const canExport = sample.length > 0 && !!selectedShape;
    csvUrl = canExport ? exportTools.csv(sample) : '';
    exportName = canExport ? exportTools.name(selectedShape, sample) : '';
  }
</script>

<main class="flex h-screen w-screen overflow-hidden">
  <AddrMap bounds={selectedShape} addresses={sample} />
  {#if selectedShape}
    <Navbar navClass="fixed w-full shadow">
      <NavBrand />
      <NavUl
        ulClass="flex flex-col p-2 mt-1 md:flex-row md:space-x-8 md:mt-0 md:text-sm md:font-medium items-center"
      >
        <NavLi>I would like</NavLi>
        <NavLi>
          <ButtonGroup class="w-full">
            <Input type="number" size="sm" id="n" bind:value={sampleSize} />
            <Button on:click={openUnitMenu}>{labelForUnit(unit)}</Button>
            <Dropdown bind:open={unitMenuOpen}>
              <DropdownItem on:click={() => setUnit('total')}>
                {labelForUnit('total')}
              </DropdownItem>
              <DropdownItem on:click={() => setUnit('pct')}>
                {labelForUnit('pct')}
              </DropdownItem>
            </Dropdown>
          </ButtonGroup>
        </NavLi>
        <NavLi>addresses from</NavLi>
        <NavLi>
          <Badge id="bound" large>
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
    <div class="absolute bottom-0 left-0 w-screen z-10 shadow">
      <SampleTable rows={sample} />
    </div>
  {/if}
  <SpeedDial class="z-10">
    <a href={csvUrl || undefined} download={exportName || undefined}>
      <SpeedDialButton name="Download CSV" disabled={!csvUrl}>
        CSV
      </SpeedDialButton>
    </a>
    <SpeedDialButton name="What is this?" on:click={() => (helpOpen = true)}>
      Help
    </SpeedDialButton>
  </SpeedDial>
  <Modal title="About" bind:open={helpOpen} autoClose>
    <Help />
  </Modal>
</main>
