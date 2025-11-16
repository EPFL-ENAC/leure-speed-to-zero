<template>
  <SectorTab
    sector-name="agriculture"
    sector-display-name="agriculture"
    :config="agricultureConfig"
  />
</template>

<script setup lang="ts">
import agricultureConfig from 'config/subtabs/agriculture.json';
import SectorTab from 'components/SectorTab.vue';
</script>
