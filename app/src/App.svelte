<script lang="ts">
  import {debounce} from 'lodash';
  import {Heading, Search, Button} from 'flowbite-svelte';
  import AutoComplete from './AutoComplete.svelte';

  // Current query string.
  let query = '';

  // List of search results from the API.
  let searchResults: Array<{
    key: string;
    label: string;
    value: {gid: number; kind: string; name: string};
  }> = [];

  // Current dropdown selection index.
  let selected = 0;

  // Load GeoJSON representing the selected item.
  const fetchShape = async (e) => {
    e.preventDefault();
    const d = searchResults[selected];
    if (!d) {
      return false;
    }

    query = '';
    const u = `http://localhost:8000/shape?kind=${d.value.kind}&gid=${d.value.gid}`;
    const res = await fetch(u);
    const data = (await res.json()) as {geom: str; kind: str; gid: number};
    const geom = JSON.parse(data.geom);
    console.log(d.name, geom);

    return false;
  };

  // Query the API with the current value of the search box.
  const search = async () => {
    if (!query) {
      selected = 0;
      searchResults = [];
      return;
    }
    const u = `http://localhost:8000/search?q=${encodeURIComponent(query)}`;
    const res = await fetch(u);
    const data = (await res.json()) as {results: string[]};
    searchResults = data.results.map((d) => ({name: d.name, value: d}));
    selected = Math.max(0, Math.min(searchResults.length - 1, selected));
  };

  // Debounce search to avoid too many requests.
  const dSearch = debounce(search, 100);

  // Handle keyboard arrow events and launch debounced search query.
  const keyHandler = (e) => {
    e.preventDefault();

    switch (e.code) {
      case 'ArrowDown':
        selected = Math.max(
          0,
          Math.min(searchResults.length - 1, selected + 1),
        );
        return;
      case 'ArrowUp':
        selected = Math.max(
          0,
          Math.min(searchResults.length - 1, selected - 1),
        );
        return;
    }

    dSearch();
    return false;
  };
</script>

<main class="flex h-screen">
  <div class="container m-auto p-16">
    <header class="py-8">
      <Heading>US Addresses Sampler</Heading>
    </header>
    <div>
      <form id="search" on:submit={fetchShape}>
        <AutoComplete options={searchResults} {selected}>
          <Search bind:value={query} on:keyup={keyHandler} />
        </AutoComplete>
      </form>
    </div>
  </div>
</main>
