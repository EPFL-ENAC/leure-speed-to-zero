<template>
  <SectorTab sector-name="lca" sector-display-name="Life cycle assessment" :config="lcaConfig" />
</template>

<script setup lang="ts">
import lcaConfig from 'config/subtabs/lca.json';
import SectorTab from 'components/SectorTab.vue';
</script>
