<script lang="ts">
  export let options: Array<{name: string; value: any}> = [];
  export let selected = 0;
</script>

<div>
  <slot />
  <div class="absolute">
    <ul>
      {#each options as opt, i}
        <li>
          {opt.name}
          {#if i == selected}*{/if}
        </li>
      {/each}
    </ul>
  </div>
</div>
