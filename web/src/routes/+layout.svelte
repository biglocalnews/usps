<script lang="ts">
  import {browser} from '$app/environment';
  import '../app.postcss';
  import {PUBLIC_GTAG} from '$env/static/public';
  import {onMount} from 'svelte';

  if (PUBLIC_GTAG) {
    onMount(() => {
      window.dataLayer = window.dataLayer || [];
      function gtag() {
        dataLayer.push(arguments);
      }
      gtag('js', new Date());

      gtag('config', PUBLIC_GTAG);
    });
  }
</script>

<svelte:head>
  {#if PUBLIC_GTAG}
    <script
      async
      src="https://www.googletagmanager.com/gtag/js?id={PUBLIC_GTAG}"
    ></script>
  {/if}
</svelte:head>

<slot />
