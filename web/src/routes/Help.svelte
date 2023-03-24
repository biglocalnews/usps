<script lang="ts">
  import {P, Heading, A} from 'flowbite-svelte';
</script>

<div>
  <P class="mb-3">
    The United States Parcel Collector (USPS) was built by Joe Nudell at <A
      href="https://biglocalnews.org/content/about/"
      rel="noopener noreferrer"
      target="_blank">Big Local News</A
    > and the
    <A
      href="https://biglocalnews.org/content/about/"
      rel="noopener noreferrer"
      target="_blank">Stanford Computational Policy Lab</A
    >
    with Leon Yin and Aaron Sankin at <A
      href="https://themarkup.org/"
      rel="noopener noreferrer"
      target="_blank">The Markup</A
    >.
  </P>
  <P class="mb-3">
    Use USPS to sample a finite number or percentage of addresses from census
    areas like counties, tracts, block groups, or other custom shapes from
    across the United States.
  </P>
  <P class="mb-3">
    <div>
      You can search for precise <A
        href="https://www.census.gov/newsroom/blogs/random-samplings/2014/07/understanding-geographic-relationships-counties-places-tracts-and-more.html"
        rel="noopener noreferrer"
        target="_blank">Census geographies</A
      > using:
    </div>
    <div class="pl-4 my-2">
      <div><code>county: queens</code> for Counties</div>
      <div><code>cousub: houston texas</code> for county subdivisions</div>
      <div><code>place: boston</code> for cities and towns</div>
      <div><code>tract: 1241234</code> for Census tracts</div>
      <div><code>bg: 12414514</code> for Census Block groups</div>
    </div>
  </P>
  <P class="mb-3">
    You can also sample addresses from custom shapes and boundaries using
    <A href="https://geojson.org/" rel="noopener noreferrer" target="_blank"
      >GeoJson</A
    >. Use the “Upload” option to select a local GeoJSON, and then choose which
    features you want to use.
  </P>
  <Heading tag="h4">Need help calculating a sample size?</Heading>
  <P class="mb-3">
    Try using an online <A
      href="https://www.calculator.net/sample-size-calculator.html"
      rel="noopener noreferrer"
      target="_blank">sample size calculator</A
    >
    based on the number of households listed on <A
      href="https://censusreporter.org"
      rel="noopener noreferrer"
      target="_blank">Census Reporter</A
    >.
  </P>
  <P class="mb-3">
    Read about why we made this tool at <A
      href="https://themarkup.org/still-loading/2023/03/02/introducing-the-united-states-place-sampler-usps"
      rel="noopener noreferrer"
      target="_blank">The Markup</A
    >.
  </P>
  <P class="mb-3">
    USPS can be accessed programmatically, read documentation for the API at <A
      href="https://usps.biglocalnews.org/docs"
      rel="noopener noreferrer"
      target="_blank">Big Local News</A
    >.
  </P>
  <Heading tag="h4">See something wrong?</Heading>
  <P class="mb-3">
    Let us know by posting an issue on <A
      href="https://github.com/biglocalnews/usps"
      rel="noopener noreferrer">GitHub</A
    >.
  </P>
</div>
