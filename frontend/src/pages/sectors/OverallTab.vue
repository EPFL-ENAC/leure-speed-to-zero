<template>
  <SectorTab :sector-name="sectorName" sector-display-name="overall" :config="overallConfig" />
</template>

<script setup lang="ts">
import overallConfig from 'config/subtabs/overall.json';
import SectorTab from 'components/SectorTab.vue';

// /!\ The overall tab does not correspond to a specific sector, hence an empty string is used. /!\
const sectorName = '';
</script>
