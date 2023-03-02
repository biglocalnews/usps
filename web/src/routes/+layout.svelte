<script lang="ts">
  import {browser} from '$app/environment';
  import '../app.postcss';
  import {env} from '$env/dynamic/public';
  import {onMount} from 'svelte';

  if (env.PUBLIC_GTAG) {
    onMount(() => {
      window.dataLayer = window.dataLayer || [];
      function gtag() {
        dataLayer.push(arguments);
      }
      gtag('js', new Date());

      gtag('config', env.PUBLIC_GTAG);
    });
  }
</script>

<svelte:head>
  {#if env.PUBLIC_GTAG}
    <script
      async
      src="https://www.googletagmanager.com/gtag/js?id={env.PUBLIC_GTAG}"
    ></script>
  {/if}
</svelte:head>

<slot />
