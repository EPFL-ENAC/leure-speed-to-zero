<template>
  <SectorTab
    sector-name="true-cost"
    sector-display-name="true-cost"
    :config="trueCostConfig"
    data-sector-name=""
  />
</template>

<script setup lang="ts">
import trueCostConfig from 'config/subtabs/true-cost.json';
import SectorTab from 'components/SectorTab.vue';

// The charts are the TCAF module's health and environmental LCA outputs, so
// the page reads the merged results, not only a single module's.
</script>
