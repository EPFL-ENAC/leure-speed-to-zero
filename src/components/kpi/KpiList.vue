<template>
  <div class="kpi-list q-pa-md">
    <div class="row q-col-gutter-md">
      <div v-for="kpi in kpis" :key="kpi.title" class="col-12 col-sm-6 col-md-4 col-lg-3">
        <KpiBox
          :title="kpi.title"
          :value="kpi.value"
          :unit="kpi.unit"
          :thresholds="kpi.thresholds"
          :maximize="kpi.maximize ?? false"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import KpiBox from './KpiBox.vue';
import { useLeverStore } from 'stores/leversStore';

interface Kpi {
  title: string;
  value: number;
  unit: string;
  thresholds: { warn: number; danger: number };
  maximize?: boolean;
}

const leverStore = useLeverStore();

const kpis = ref<Kpi[]>([]);

// Generate some random KPI data for now
function generateKpiData() {
  kpis.value = [
    {
      title: 'CO2 Emissions',
      value: Math.random() * 150,
      unit: 'Mt',
      thresholds: { warn: 80, danger: 120 },
    },
    {
      title: 'Renewable Energy Share',
      value: Math.random() * 100,
      unit: '%',
      thresholds: { warn: 60, danger: 80 },
      maximize: true,
    },
    {
      title: 'Energy Demand',
      value: Math.random() * 500,
      unit: 'TWh',
      thresholds: { warn: 400, danger: 450 },
    },
    {
      title: 'Investment Cost',
      value: Math.random() * 2000,
      unit: 'B€',
      thresholds: { warn: 1500, danger: 1800 },
    },
  ];
}

watch(() => leverStore.levers, generateKpiData, { immediate: true });

onMounted(() => {
  generateKpiData();
});
</script>

<style lang="scss" scoped>
.kpi-list {
  width: 100%;
}
</style>
