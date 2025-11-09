<template>
  <div v-if="kpis.length > 0" class="kpi-list q-pa-md">
    <div class="kpi-container">
      <div v-for="(kpi, index) in kpis" :key="`${kpi.route}-${index}`" class="kpi-item">
        <KpiBox v-bind="kpi" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import KpiBox from './KpiBox.vue';
import { type KPI } from 'src/utils/sectors';

const { kpis } = defineProps<{
  kpis: KPI[];
}>();
</script>

<style lang="scss" scoped>
.kpi-list {
  width: 100%;
}

.kpi-container {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: space-around;
  align-items: start;
}
</style>
