<script lang="ts">
  import {Heading, Search, Button} from 'flowbite-svelte';

  let query = '';

  const search = (e) => {
    e.preventDefault();
    query = '';
    // TKTK - run query
    console.log(query);
    return false;
  };
</script>

<main class="flex h-screen">
  <div class="container m-auto p-16">
    <header class="py-8">
      <Heading>US Addresses Sampler</Heading>
    </header>
    <div>
      <form id="search" on:submit={search}>
        <Search bind:value={query}>
          <Button type="submit">Sample</Button>
        </Search>
      </form>
    </div>
  </div>
</main>
