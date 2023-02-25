<script lang="ts">
  import {Badge} from 'flowbite-svelte';
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

  const colorize = (kind: string) => {
    switch (kind) {
      case 'state':
        return 'red';
      case 'county':
        return 'green';
      case 'cousub':
        return 'blue';
      case 'place':
        return 'purple';
      case 'tract':
        return 'yellow';
      case 'zcta5':
        return 'pink';
      default:
        return 'dark';
    }
  };

  const labelize = (kind: string) => {
    switch (kind) {
      case 'state':
        return 'State';
      case 'county':
        return 'County';
      case 'cousub':
        return 'County Subdivision';
      case 'place':
        return 'Place';
      case 'tract':
        return 'Tract';
      case 'zcta5':
        return 'Zip Code';
      default:
        return kind;
    }
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
          <span>{opt.name}</span>
          <span class="text-stone-300">{opt.secondary}</span>
          <div class="float-right">
            <Badge color={colorize(opt.kind)}>{labelize(opt.kind)}</Badge>
          </div>
        </li>
      {/each}
    </ul>
  </div>
</div>
