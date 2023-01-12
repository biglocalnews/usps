<script lang="ts">
  import {Heading, Button} from 'flowbite-svelte';
  import Search from './Search.svelte';
  import * as api from './api.ts';

  // Load GeoJSON representing the selected item.
  const fetchShape = async (e) => {
    const res = await api.fetchShape(e.detail);
    console.log(res);
  };
</script>

<main class="flex h-screen">
  <div class="container m-auto p-16">
    <header class="py-8">
      <Heading>US Addresses Sampler</Heading>
    </header>
    <div>
      <Search on:select={fetchShape} />
    </div>
  </div>
</main>
