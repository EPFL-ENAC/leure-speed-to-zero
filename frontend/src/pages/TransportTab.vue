<template>
  <SectorTab sector-name="transport" sector-display-name="transport" :config="transportConfig" />
</template>

<script setup lang="ts">
import transportConfig from 'config/subtabs/transport.json';
import SectorTab from 'components/SectorTab.vue';
</script>
