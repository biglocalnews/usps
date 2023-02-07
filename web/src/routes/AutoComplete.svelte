<script lang="ts">
  import {createEventDispatcher} from 'svelte';
  import type {ShapePointer} from '../lib/api.ts';

  /**
   * Array of options to show.
   */
  export let options: ShapePointer[] = [];
  /**
   * Index of selected option.
   */
  export let selected = 0;
  /**
   * Whether autocomplete component is visible.
   */
  export let visible = false;

  const dispatch = createEventDispatcher();

  // Handle selecting option with the mouse.
  const handleClick = (e, i) => {
    e.preventDefault();
    dispatch('select', i);
  };
</script>

<div class="relative">
  <slot />
  <div
    class="absolute shadow bg-white w-full rounded overflow-hidden"
    class:hidden={!visible || !options.length}
  >
    <ul class="overflow-y-auto">
      {#each options as opt, i}
        <li
          class="py-3 px-2 cursor-pointer hover:bg-sky-400 hover:text-white"
          class:text-white={selected === i}
          class:bg-sky-500={selected === i}
          on:mousedown={(e) => handleClick(e, i)}
        >
          {opt.name}
        </li>
      {/each}
    </ul>
  </div>
</div>
