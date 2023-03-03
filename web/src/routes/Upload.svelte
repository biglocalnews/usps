<script lang="ts">
  import {onMount, createEventDispatcher} from 'svelte';
  import {
    Fileupload,
    Modal,
    Table,
    TableBody,
    TableBodyRow,
    TableBodyCell,
    TableHead,
    TableHeadCell,
  } from 'flowbite-svelte';
  import {getFuzzyFeatureProp} from '$lib/getFeatureName';

  const dispatch = createEventDispatcher();
  let uploadFiles: FileList[] = [];
  let collectionSet: GeoJSON.Feature<GeoJSON.MultiPolygon, {}> | null = null;

  // Fire "select" event with valid shape
  const acceptShape = (json: GeoJSON.Feature<GeoJSON.MultiPolygon, {}>) => {
    const name = getFuzzyFeatureProp(json.properties, 'name');
    if (!name) {
      json.properties['$$tmpName'] = uploadFiles[0].name;
    }
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
        collectionSet = json.features.slice().sort((a, b) => {
          const aName = getFuzzyFeatureProp(a, 'name', 'id');
          const bName = getFuzzyFeatureProp(b, 'name', 'id');
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
  <Modal bind:open={collectionSet}>
    <Table hoverable>
      <TableHead>
        <TableHeadCell>Feature</TableHeadCell>
      </TableHead>
      <TableBody>
        {#each collectionSet as feature, i}
          <TableBodyRow on:click={() => acceptShape(feature)}>
            <TableBodyCell>
              {getFuzzyFeatureProp(feature.properties, 'name', 'id') || i}
            </TableBodyCell>
          </TableBodyRow>
        {/each}
      </TableBody>
    </Table>
  </Modal>
</div>
