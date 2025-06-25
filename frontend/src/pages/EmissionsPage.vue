<template>
  <q-page padding>
    <div class="q-pa-md">
      <h1 class="text-h4 q-mb-md">Emissions</h1>
      <EmissionsGraph />
    </div>
  </q-page>
</template>

<script setup lang="ts">
import EmissionsGraph from 'components/graphs/EmissionsGraph.vue';
</script>
