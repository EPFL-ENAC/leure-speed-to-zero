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
  sector: string;
  route: string;
  maximize?: boolean;
  info?: string;
}

const leverStore = useLeverStore();

const kpis = ref<Kpi[]>([]);

// Generate some random KPI data for now
function generateKpiData() {
  kpis.value = [
     {
      title: 'CO2 emissions',
      value: Math.random() * 2000,
      unit: 'Mt',
      sector: 'Buildings',
      maximize: false,
      route: 'building-types-emissions',
      thresholds: { warn: 1500, danger: 1800 },
    },
    {
      title: 'Energy Demand for Space Heating',
      value: Math.random() * 500,
      unit: 'TWh',
      thresholds: { warn: 400, danger: 450 },
      sector: 'Buildings',
      route: 'energy-carriers',
      maximize: false,
      info: 'This indicator measures the total annual energy delivered for space heating in residential buildings (in TWh). It accounts for all heating sources—including gas, heating oil, biomass, and electricity for heat pumps—but excludes the ambient heat extracted by heat pumps, reflecting only the actual energy input required for heating.',
    },
    {
      title: 'A-C Class',
      value: Math.random() * 150,
      unit: '%',
      thresholds: { warn: 90, danger: 70 },
      sector: 'Buildings',
      route: 'building-types-area',
      maximize: true,
      info: 'Share of residential floor area with high-quality thermal envelopes (categories A, B, C) in 2050. The rating reflects the building envelope’s thermal resistance—including insulation of walls, roof, floor, windows, as well as thermal bridges and building form—based on the CECB classification (A = best, G = worst). A higher share indicates better energy efficiency potential, improved occupant comfort, and reduced heating demand in the residential stock.',
    },
    {
      title: 'Unrenovated Envelope Share',
      value: Math.random() * 100,
      unit: '%',
      thresholds: { warn: 5, danger: 15 },
      sector: 'Buildings',
      route: 'renovation-construction',
      maximize: false,
      info: 'Share of residential floor area that has not undergone an envelope renovation. This includes buildings whose envelope efficiency class has not improved since construction, typically indicating poor or outdated thermal performance. A high value suggests large remaining potential for energy savings and carbon reduction in the existing residential stock.',
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
