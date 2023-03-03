<script lang="ts">
  import {onMount, createEventDispatcher} from 'svelte';
  import {
    Helper,
    Fileupload,
    Modal,
    Table,
    TableBody,
    TableBodyRow,
    TableBodyCell,
    TableHead,
    TableHeadCell,
  } from 'flowbite-svelte';
  import {getFeatureName} from '$lib/getFeatureName';

  const dispatch = createEventDispatcher();
  let uploadFiles: FileList[] = [];
  let collectionSet: GeoJSON.Feature<GeoJSON.MultiPolygon, {}> | null = null;

  // Fire "select" event with valid shape
  const acceptShape = (json: GeoJSON.Feature<GeoJSON.MultiPolygon, {}>) => {
    const name = getFeatureName(json.properties);
    dispatch('select', json);
    uploadFiles = [];
    collectionSet = null;
  };

  // Upload a custom geometry
  const uploadShape = async () => {
    if (uploadFiles.length === 0) {
      return;
    }

    const t = await uploadFiles[0].text();
    try {
      const json = JSON.parse(t);
      if (json.type === 'FeatureCollection') {
        // Sort the features alphabetically.
        json.features.forEach((f, i) => {
          getFeatureName(f.properties, `${uploadFiles[0].name}-${i}`);
        });

        collectionSet = json.features.slice().sort((a, b) => {
          const aName = getFeatureName(a.properties);
          const bName = getFeatureName(b.properties);
          if (aName === bName) {
            return 0;
          }
          return aName < bName ? -1 : 1;
        });
        return;
      } else if (json.type !== 'Feature') {
        throw new Error('Only GeoJSON features are supported at this time.');
      }
      acceptShape(json);
    } catch (e) {
      dispatch('error', e);
      uploadFiles = [];
    }
  };

  $: {
    if (uploadFiles.length > 0) {
      uploadShape();
    }
  }
</script>

<div>
  <Fileupload bind:files={uploadFiles} />
  <Modal bind:open={collectionSet} title="Feature Collection">
    <Helper
      >Select the feature in this collection you want to sample from.</Helper
    >
    <Table hoverable>
      <TableHead>
        <TableHeadCell>Name</TableHeadCell>
      </TableHead>
      <TableBody>
        {#each collectionSet as feature, i}
          <TableBodyRow on:click={() => acceptShape(feature)}>
            <TableBodyCell
              tdClass="px-6 py-4 whitespace-nowrap font-medium cursor-pointer"
            >
              <div
                class="truncate max-w-xl"
                title={getFeatureName(feature.properties)}
              >
                {getFeatureName(feature.properties)}
              </div>
            </TableBodyCell>
          </TableBodyRow>
        {/each}
      </TableBody>
    </Table>
  </Modal>
</div>
