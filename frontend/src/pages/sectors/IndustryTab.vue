<template>
  <SectorTab sector-name="industry" sector-display-name="industry" :config="industryConfig" />
</template>

<script setup lang="ts">
import industryConfig from 'config/subtabs/industry.json';
import SectorTab from 'components/SectorTab.vue';
</script>
