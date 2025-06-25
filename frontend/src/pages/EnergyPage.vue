<template>
  <q-page padding>
    <div class="q-pa-md">
      <h1 class="text-h4 q-mb-md">Energy</h1>
      <EnergyGraph />
    </div>
  </q-page>
</template>

<script setup lang="ts">
import EnergyGraph from 'components/graphs/EnergyGraph.vue';
</script>
