<template>
  <SectorTab sector-name="buildings" sector-display-name="buildings" :config="buildingsConfig" />
</template>

<script setup lang="ts">
import buildingsConfig from 'config/subtabs/buildings.json';
import SectorTab from 'components/SectorTab.vue';
</script>
