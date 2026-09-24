<template>
  <SectorTab
    sector-name="dietary-habits"
    sector-display-name="dietary-habits"
    :config="dietaryHabitsConfig"
    data-sector-name="dietary-habits"
  />
</template>

<script setup lang="ts">
import dietaryHabitsConfig from 'config/subtabs/dietary-habits.json';
import SectorTab from 'components/SectorTab.vue';

// The charts mix outputs of several modules (diet, TCAF health, land use), so
// the page reads the merged results, not only the dietary-habits ones.
// data-sector-name="dietary-habits" routes through leversStore's dedicated
// branch, which also adds a synthetic "BAU (2050)" row for the diet snapshot
// chart (see BAU_2050_SNAPSHOT_YEAR).
</script>
