<script lang="ts">
  import 'mapbox-gl/dist/mapbox-gl.css';
  import mapboxgl from 'mapbox-gl';
  import extent from '@mapbox/geojson-extent';
  import {onMount, createEventDispatcher} from 'svelte';
  import type {Shape, Address} from './api.ts';
  import * as config from './config.ts';

  const dispatch = createEventDispatcher();

  export let bounds: Shape | null = null;
  export let addresses: Address[] = [];
  export let popupData: Address | null = null;

  mapboxgl.accessToken = config.mapboxToken;

  // Mapbox map - not available until the component mounts.
  let map: mapboxgl.Map | null = null;
  // Flag to indicate when mapbox map is ready.
  let ready = false;
  let popup: mapboxgl.Popup | null = null;

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

    map.on('load', (e) => {
      ready = true;
      dispatch('ready', e);
    });
  });

  // Manage popup
  $: {
    if (ready) {
      if (!popupData) {
        if (popup) {
          popup.remove();
          popup = null;
        }
      } else {
        if (!popup) {
          popup = new mapboxgl.Popup();
          popup.addTo(map);
          popup.on('close', () => {
            popupData = null;
          });
        }
        popup.setLngLat(popupData.geometry.coordinates);
        popup.setHTML(`<div>${popupData.properties.address}</div>`);
        map.flyTo({zoom: 13, center: popupData.geometry.coordinates});
      }
    }
  }

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
        const collection = {
          type: 'FeatureCollection',
          features: addresses,
        };
        map
          .addSource('addresses', {
            type: 'geojson',
            data: collection,
          })
          .addLayer({
            id: 'points',
            type: 'circle',
            source: 'addresses',
            paint: {
              'circle-color': '#4d7c0f', // lime-700
              'circle-radius': 2,
            },
          })
          // Re-center map on bounds, not the address collection. The extent
          // of the address collection is similar, but probably very slightly
          // different, which would cause an unpleasant jitter.
          .fitBounds(extent(bounds));
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
              'line-color': '#b91c1c', // red-700
            },
          })
          .addLayer({
            id: 'shade',
            type: 'fill',
            source: 'bounds',
            layout: {},
            paint: {
              'fill-color': '#d9f99d', // lime-200
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
