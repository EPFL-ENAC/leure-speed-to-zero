<template>
  <SectorTab sector-name="energy" sector-display-name="energy" :config="energyConfig" />
</template>

<script setup lang="ts">
import energyConfig from 'config/subtabs/energy.json';
import SectorTab from 'components/SectorTab.vue';
</script>
