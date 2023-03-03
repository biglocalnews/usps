<script lang="ts">
  import {browser} from '$app/environment';
  import {fly, fade} from 'svelte/transition';
  import {
    Fileupload,
    Heading,
    Helper,
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
    Tabs,
    TabItem,
  } from 'flowbite-svelte';
  import {ChevronDown, Sparkles, QuestionMarkCircle} from 'svelte-heros-v2';
  import Search from './Search.svelte';
  import AddrMap from './AddrMap.svelte';
  import SampleTable from './SampleTable.svelte';
  import Help from './Help.svelte';
  import Upload from './Upload.svelte';
  import {getFeatureName} from '$lib/getFeatureName';
  import * as api from '../lib/api.ts';
  import * as exportTools from '../lib/export.ts';
  import type {Address, Shape, SampleSizeUnit} from '../lib/api.ts';

  const showUpload = browser && document.location.search === '?new';
  let searchMode: 'search' | 'upload' = 'search';
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
    } catch (err) {
      error = err;
      return;
    }
  };

  // Handle a direct upload of a GeoJSON feature.
  const uploadShape = async (e) => {
    mapCoord = null;
    sample = [];
    error = null;
    selectedShape = e.detail;
  };

  // Load sample data in the current boundary.
  const fetchSample = async (e) => {
    loading = true;
    error = null;
    mapCoord = null;
    sample = [];
    try {
      const sampleRes = await api.sample(selectedShape, sampleSize, unit);
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
    searchMode = 'search';
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
                {getFeatureName(selectedShape.properties, 'name') ||
                  'Selected area'}
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
          {#if showUpload}
            <Tabs
              contentClass="p-4 bg-gray-50/75 rounded-b-lg rounded-tr-lg dark:bg-gray-800/75"
              inactiveClasses="p-4 text-gray-500 rounded-t-lg hover:text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-300 bg-white"
            >
              <TabItem
                open={searchMode === 'search'}
                on:click={(searchMode = 'search')}
                title="Search"
              >
                <Search on:select={fetchShape} />
                <Helper
                  class="text-s font-normal text-sky-600 dark:text-sky-300 pt-4 rounded"
                  >Search for census geometries like counties, places, and
                  tracts. Try: "Glover, Vermont."</Helper
                >
              </TabItem>
              <TabItem
                open={searchMode === 'upload'}
                on:click={(searchMode = 'upload')}
                title="Upload"
              >
                <Upload on:select={uploadShape} />
                <Helper
                  class="text-s font-normal text-sky-600 dark:text-sky-300 rounded pt-4 rounded"
                >
                  Upload a file containing a GeoJSON Feature from your computer
                  to use as the sampling area.
                </Helper>
              </TabItem>
            </Tabs>
          {:else}
            <Search on:select={fetchShape} />
          {/if}
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
