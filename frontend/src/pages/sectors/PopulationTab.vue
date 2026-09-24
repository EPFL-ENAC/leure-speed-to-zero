<template>
  <SectorTab
    sector-name="population"
    sector-display-name="population"
    :config="populationConfig"
    data-sector-name="population"
  />
</template>

<script setup lang="ts">
import populationConfig from 'config/subtabs/population.json';
import SectorTab from 'components/SectorTab.vue';

// data-sector-name="population" routes through leversStore's dedicated branch,
// which adds the derived annual change and growth rate these charts need.
</script>
