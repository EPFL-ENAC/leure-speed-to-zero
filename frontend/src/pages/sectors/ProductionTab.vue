<template>
  <SectorTab
    sector-name="production"
    sector-display-name="production"
    :config="productionConfig"
    data-sector-name="production"
  />
</template>

<script setup lang="ts">
import productionConfig from 'config/subtabs/production.json';
import SectorTab from 'components/SectorTab.vue';

// data-sector-name="production" routes through leversStore's dedicated branch,
// which reads the agriculture module's output and adds the derived
// import/export/self-sufficiency fields these charts need.
</script>
