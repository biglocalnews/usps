<script lang="ts">
  import type {ShapePointer} from './api.ts';
  import {createEventDispatcher} from 'svelte';

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

<div>
  <slot />
  <div class="absolute" class:hidden={!visible}>
    <ul>
      {#each options as opt, i}
        <li on:mousedown={(e) => handleClick(e, i)}>
          {opt.name}
          {#if i == selected}*{/if}
        </li>
      {/each}
    </ul>
  </div>
</div>
