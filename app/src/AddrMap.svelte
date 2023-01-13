<script lang="ts">
  import 'mapbox-gl/dist/mapbox-gl.css';
  import mapboxgl from 'mapbox-gl';
  import extent from '@mapbox/geojson-extent';
  import {onMount} from 'svelte';
  import type {Shape, Address} from './api.ts';
  import * as config from './config.ts';

  export let bounds: Shape | null = null;
  export let addresses: Address[] = [];

  mapboxgl.accessToken = config.mapboxToken;

  // Mapbox map - not available until the component mounts.
  let map: mapboxgl.Map | null = null;
  // Flag to indicate when mapbox map is ready.
  let ready = false;

  // Initial viewport parameters -- this centers most of the contiguous US.
  const initialZoom = {
    zoom: 3,
    center: [-98.5795, 39.8283],
  };

  // Render map when component loads.
  onMount(() => {
    map = new mapboxgl.Map({
      container: 'map',
      style: 'mapbox://styles/mapbox/light-v11',
      ...initialZoom,
    });

    map.on('load', () => {
      ready = true;
    });
  });

  // Update the address sample layer when sample/map are updated.
  $: {
    if (ready) {
      if (map.getLayer('points')) {
        map.removeLayer('points');
      }
      if (map.getSource('addresses')) {
        map.removeSource('addresses');
      }

      if (addresses.length) {
        map
          .addSource('addresses', {
            type: 'geojson',
            data: {
              type: 'FeatureCollection',
              features: addresses,
            },
          })
          .addLayer({
            id: 'points',
            type: 'circle',
            source: 'addresses',
            paint: {
              'circle-color': '#f00',
              'circle-radius': 3,
            },
          });
      }
    }
  }

  // Update the boundary layer when bounds/map are updated.
  $: {
    if (ready) {
      if (map.getLayer('outline')) {
        map.removeLayer('outline');
      }
      if (map.getLayer('shade')) {
        map.removeLayer('shade');
      }
      if (map.getSource('bounds')) {
        map.removeSource('bounds');
      }

      if (bounds) {
        map
          .addSource('bounds', {
            type: 'geojson',
            data: bounds,
          })
          .addLayer({
            id: 'outline',
            type: 'line',
            source: 'bounds',
            layout: {},
            paint: {
              'line-color': '#f00',
            },
          })
          .addLayer({
            id: 'shade',
            type: 'fill',
            source: 'bounds',
            layout: {},
            paint: {
              'fill-color': '#00f',
              'fill-opacity': 0.1,
            },
          })
          .fitBounds(extent(bounds));
      }
    }
  }
</script>

<style lang="postcss">
  #map {
    position: fixed;
  }
</style>

<div id="map" class="z-0 absolute inset-0 h-screen w-screen" />
