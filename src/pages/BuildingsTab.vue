<template>
  <q-page padding>
    <div class="row">
      <div class="col-12">
        <h1 class="text-h4 q-mb-md">Buildings</h1>
      </div>
    </div>

    <q-tabs
      v-model="currentTab"
      class="text-primary q-mb-lg"
      no-caps
      active-color="primary"
      indicator-color="primary"
      align="justify"
    >
      <q-tab v-for="tab in subtabs" :key="tab.route" :name="tab.route" :label="tab.title" />
    </q-tabs>

    <div v-if="!modelResults" class="graph-placeholder q-pa-xl">
      <q-icon name="show_chart" size="4rem" />
      <p>Run the model to see buildings data</p>
      <q-btn
        label="Run Model"
        color="primary"
        :loading="isLoading"
        @click="runModel"
        class="q-mt-md"
      />
    </div>

    <q-tab-panels v-else v-model="currentTab" animated>
      <q-tab-panel v-for="tab in subtabs" :key="tab.route" :name="tab.route">
        <div class="row q-col-gutter-md">
          <div v-for="chartId in tab.charts" :key="chartId" class="col-12 col-md-6">
            <chart-card :chart-config="charts[chartId as ChartId]" :model-data="modelResults" />
          </div>
        </div>
      </q-tab-panel>
    </q-tab-panels>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useLeverStore } from 'stores/leversStore';
import buildingsConfig from 'config/subtabs/buildings.json';
import ChartCard from 'components/graphs/ChartCard.vue';

const router = useRouter();
const route = useRoute();

// Define types for the charts configuration
type ChartConfigs = typeof buildingsConfig.charts;
type ChartId = keyof ChartConfigs;

const subtabs = buildingsConfig.subtabs;
// No need for type assertion since TypeScript can infer this correctly
const charts = buildingsConfig.charts;
const leverStore = useLeverStore();

// Tab state
const currentTab = ref(
  typeof route.params.subtab === 'string' ? route.params.subtab : subtabs[0]?.route,
);

// Watch for tab changes to update URL
watch(currentTab, async (newTab) => {
  try {
    await router.push({ name: 'buildings', params: { subtab: newTab } });
  } catch (error) {
    console.error('Navigation error:', error);
  }
});

// Properly typed computed property
const modelResults = computed(() => {
  const newData = leverStore.buildings;

  return newData;
});

// let previousResults: typeof leverStore.buildings = null;
// watch(
//   () => leverStore.buildings,
//   (newData) => {
//     if (!newData?.countries?.Vaud || !previousResults?.countries?.Vaud) {
//       previousResults = JSON.parse(JSON.stringify(newData)); // Deep copy
//       return;
//     }

//     const newYears = newData.countries.Vaud;
//     const prevYears = previousResults.countries.Vaud;

//     // Check each year's data
//     newYears.forEach((newYearData, index) => {
//       if (index >= prevYears.length) return;

//       const year = newYearData.year;
//       const prevYearData = prevYears[index];
//       if (!prevYearData) return;
//       // Compare all properties
//       Object.keys(newYearData).forEach((key) => {
//         const newValue = newYearData[key] as number;
//         const prevValue = prevYearData[key] as number;
//         const diff = Math.abs(newValue - prevValue);
//         const change = diff / Math.max(Math.abs(newValue), Math.abs(prevValue));
//         if (change > 0.01) {
//           console.log({ year, key, newValue, prevValue, diff, change });
//         }
//       });
//     });

//     // Store current data for next comparison
//     previousResults = JSON.parse(JSON.stringify(newData));
//   },
//   { deep: true },
// );

const isLoading = computed(() => leverStore.isLoading);

// Method to run the model
async function runModel() {
  try {
    await leverStore.runModel();
  } catch (error) {
    console.error('Error running model:', error);
  }
}
</script>

<style lang="scss" scoped>
.graph-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  background-color: #f5f5f5;
  border-radius: 8px;
  color: #9e9e9e;
}
</style>
