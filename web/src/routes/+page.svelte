<script lang="ts">
  import {fly, fade} from 'svelte/transition';
  import {
    Heading,
    Dropdown,
    DropdownItem,
    Checkbox,
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
  import {ChevronDown, Sparkles, QuestionMarkCircle} from 'svelte-heros-v2';
  import Search from './Search.svelte';
  import AddrMap from './AddrMap.svelte';
  import SampleTable from './SampleTable.svelte';
  import Help from './Help.svelte';
  import * as api from '../lib/api.ts';
  import * as exportTools from '../lib/export.ts';
  import type {Address, Shape, SampleSizeUnit} from '../lib/api.ts';

  let ready = false;
  let sample: Address[] = [];
  let loading = false;
  let sampleSize = 200;
  let selectedShape: Shape | null = null;
  let unit: SampleSizeUnit = 'total';
  let unitMenuOpen = false;
  let csvUrl = '';
  let exportName = '';
  let helpOpen = false;
  let error: Error | null = null;
  let mapCoord: Address | null = null;

  // Load GeoJSON representing the selected item.
  const fetchShape = async (e) => {
    mapCoord = null;
    sample = [];
    error = null;
    selectedShape = null;
    try {
      selectedShape = await api.fetchShape(e.detail);
    } catch (e) {
      error = e;
      return;
    }
  };

  // Load sample data in the current boundary.
  const fetchSample = async (e) => {
    loading = true;
    error = null;
    mapCoord = null;
    sample = [];
    try {
      const sampleRes = await api.sample(
        selectedShape.properties,
        sampleSize,
        unit,
      );
      sample = sampleRes.addresses;
      loading = false;
    } catch (e) {
      error = e;
      loading = false;
      return;
    }
  };

  // Clear current error message.
  const clearError = () => {
    error = null;
  };

  // Clear current boundary / sample.
  const clearSelection = (e) => {
    if (loading) {
      return;
    }
    mapCoord = null;
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

  const setMapCoord = (e) => {
    mapCoord = e.detail;
  };

  $: {
    const canExport = sample.length > 0 && !!selectedShape;
    csvUrl = canExport ? exportTools.csv(sample) : '';
    exportName = canExport ? exportTools.name(selectedShape, sample) : '';
  }

  // Indicate that subcomponents are ready.
  const setReady = () => {
    ready = true;
  };
</script>

<style lang="postcss">
  /* Unfortunately the flowbite-svelte components are hard to customize.
     This is a hack to make sure the button text doesn't wrap.
     */
  :global(#unitbtn) {
    flex-shrink: 0;
  }

  main {
    opacity: 0;
  }
  main.ready {
    opacity: 1;
  }
</style>

<div>
  {#if !ready}
    <div class="flex h-screen w-screen absolute left-0 top-0">
      <div class="m-auto" transition:fade={{duration: 200}}><Spinner /></div>
    </div>
  {/if}
  <main
    class="flex h-screen w-screen overflow-hidden transition-[opacity]"
    class:ready
  >
    <AddrMap
      bounds={selectedShape}
      popupData={mapCoord}
      addresses={sample}
      on:ready={setReady}
    />
    {#if selectedShape}
      <div
        class="w-full fixed shadow"
        transition:fly={{y: -200, duration: 200}}
      >
        <Navbar
          navDivClass="w-full flex flex-nowrap justify-between items-center"
        >
          <NavBrand
            ><Heading tag="h1" customSize="text-xl" class="mx-4"
              >U.S.P.S.</Heading
            ></NavBrand
          >
          <NavUl
            ulClass="flex flex-col p-2 mt-1 md:flex-row md:space-x-8 md:mt-0 md:text-sm md:font-medium items-center"
          >
            <NavLi>I would like</NavLi>
            <NavLi>
              <ButtonGroup class="w-full">
                <Input type="number" size="sm" id="n" bind:value={sampleSize} />
                <Button on:click={openUnitMenu} id="unitbtn"
                  >{labelForUnit(unit)}</Button
                >
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
                  <Spinner class="ml-2" size="4" />
                {:else}
                  <Sparkles class="ml-2" size="16" />
                {/if}
              </Button>
            </NavLi>
          </NavUl>
        </Navbar>
      </div>
    {/if}
    {#if !selectedShape}
      <div
        class="container m-auto p-16 z-10"
        transition:fly={{y: 200, duration: 200}}
      >
        <header class="py-8">
          <Heading>US Place Sampler</Heading>
        </header>
        <div>
          <Search on:select={fetchShape} />
        </div>
      </div>
    {/if}
    {#if sample.length}
      <div
        class="absolute bottom-0 left-0 w-screen z-10 shadow"
        transition:fly={{y: 200, duration: 200}}
      >
        <SampleTable on:hover={setMapCoord} rows={sample} />
      </div>
    {/if}
    <SpeedDial class="z-10">
      <a
        href={csvUrl || undefined}
        download={exportName ? `${exportName}.csv` : undefined}
      >
        <SpeedDialButton name="Download CSV" disabled={!csvUrl}>
          CSV
        </SpeedDialButton>
      </a>
      <SpeedDialButton
        name="About this tool"
        on:click={() => (helpOpen = true)}
      >
        <QuestionMarkCircle />
      </SpeedDialButton>
    </SpeedDial>
    <Modal title="About" bind:open={helpOpen} autoClose>
      <Help />
    </Modal>
    <Modal title="Error" bind:open={error} autoClose>
      <p>An error occurred! {error.message}</p>
    </Modal>
  </main>
</div>
