<template>
  <SectorTab sector-name="forestry" sector-display-name="forestry" :config="forestryConfig" />
</template>

<script setup lang="ts">
import forestryConfig from 'config/subtabs/forestry.json';
import SectorTab from 'components/SectorTab.vue';
</script>
