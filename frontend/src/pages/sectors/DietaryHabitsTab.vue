<template>
  <SectorTab
    sector-name="dietary-habits"
    sector-display-name="dietary-habits"
    :config="dietaryHabitsConfig"
    data-sector-name=""
  />
</template>

<script setup lang="ts">
import dietaryHabitsConfig from 'config/subtabs/dietary-habits.json';
import SectorTab from 'components/SectorTab.vue';

// The charts mix outputs of several modules (diet, TCAF health, land use), so
// the page reads the merged results, not only the dietary-habits ones.
</script>
