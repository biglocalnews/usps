<script lang="ts">
  import {onMount, createEventDispatcher} from 'svelte';
  import {debounce} from 'lodash-es';
  import {Search, Helper} from 'flowbite-svelte';
  import AutoComplete from './AutoComplete.svelte';
  import * as api from '../lib/api.ts';

  /**
   * Minimum length for autocomplete search queries.
   */
  export let minLength = 3;

  const dispatch = createEventDispatcher();

  // Current query string.
  let query = '';

  // Current dropdown selection index.
  let selected = 0;

  // Whether autocomplete is visible.
  let visible = true;

  // List of search results from the API.
  let searchResults: api.ShapePointer[] = [];

  // TS of last query fired.
  let mark = 0;

  // Dispatch the "select" event to report the chosen option.
  const doSelect = () => {
    const opt = searchResults[selected];
    if (!opt) {
      return;
    }

    // Reset state
    query = '';
    searchResults = [];
    visible = false;

    dispatch('select', opt);
  };

  // Ensure selected index doesn't go out of bounds on the results list.
  const clampSelectedIndex = (newIdx: number) => {
    return Math.max(0, Math.min(searchResults.length - 1, newIdx));
  };

  // Query the API with the current value of the search box.
  const search = async () => {
    // Minimum length ensures we don't flood API with short/uninformative queries
    if (!query || query.length < minLength) {
      selected = 0;
      searchResults = [];
      return;
    }
    const t = Date.now();
    mark = t;
    const results = await api.search(query);
    // If this was still the latest query, then update results in the UI.
    // Otherwise we'll just discard them. `mark` might have been changed while
    // we were waiting for results.
    if (mark === t) {
      searchResults = results;
      selected = clampSelectedIndex(selected);
    }
  };

  // Debounce search to avoid too many requests.
  const dSearch = debounce(search, 100);

  // Handle keyboard arrow events and launch debounced search query.
  const keyHandler = (e) => {
    visible = true;
    switch (e.code) {
      case 'ArrowDown':
        selected = clampSelectedIndex(selected + 1);
        e.preventDefault();
        return;
      case 'ArrowUp':
        selected = clampSelectedIndex(selected - 1);
        e.preventDefault();
        return;
      case 'Enter':
        doSelect();
        e.preventDefault();
        return;
      default:
        // Queue a search request with new value. Only bother if the key will
        // change the content of the query. Notably, punctuation is omitted
        // since it doesn't actually impact the search results.
        if (/^(Key|Digit|Backspace|Delete|Space)/.test(e.code)) {
          dSearch();
        }
        return;
    }
  };

  // Handle click on a dropdown option.
  const clickHandler = (e) => {
    // Set the selection to whichever index was clicked on, then submit.
    selected = e.detail;
    doSelect();
  };

  // Hide autocomplete
  const hide = () => {
    visible = false;
  };

  // Show autocomplete
  const show = () => {
    visible = true;
  };

  // Set focus on the search input when the component mounts.
  onMount(() => {
    document.querySelector('input[type=search]').focus();
  });
</script>

<div>
  <AutoComplete
    options={searchResults}
    {selected}
    {visible}
    on:select={clickHandler}
  >
    <Search
      name="geoinput"
      bind:value={query}
      on:keydown={keyHandler}
      on:blur={hide}
      on:focus={show}
      placeholder="Where would you like to sample?"
    />
  </AutoComplete>
  <Helper
    class="text-s font-normal text-sky-600 dark:text-sky-300 pt-1 bg-white/50 rounded"
    >You can search for cities, towns, counties, or states. Try: "Glover,
    Vermont."</Helper
  >
</div>
