<template>
  <div>
    <kpi-list :kpis="kpis" />

    <q-tabs v-model="currentTab" outside-arrows active-color="primary" no-caps align="justify">
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

    <template v-else>
      <q-tab-panels v-model="currentTab" animated>
        <q-tab-panel v-for="tab in subtabs" :key="tab.route" :name="tab.route">
          <div class="row q-col-gutter-md">
            <div v-for="chartId in tab.charts" :key="chartId" class="col-12">
              <chart-card :chart-config="charts[chartId as ChartId]" :model-data="modelResults" />
            </div>
          </div>
        </q-tab-panel>
      </q-tab-panels>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useLeverStore } from 'stores/leversStore';
import buildingsConfig from 'config/subtabs/buildings.json';
import KpiList from 'src/components/kpi/KpiList.vue';
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
  typeof route.params.subtab === 'string' && route.params.subtab
    ? route.params.subtab
    : subtabs[0]?.route,
);

// If no subtab is present in the URL, redirect to the default one.
if (!route.params.subtab && subtabs[0]?.route) {
  void router.replace({ name: 'buildings', params: { subtab: subtabs[0]?.route } });
}

// Watch for tab changes to update URL
watch(currentTab, async (newTab) => {
  if (newTab && newTab !== route.params.subtab) {
    try {
      await router.push({ name: 'buildings', params: { subtab: newTab } });
    } catch (error) {
      console.error('Navigation error:', error);
    }
  }
});

// Properly typed computed property
const modelResults = computed(() => {
  const newData = leverStore.buildings;
  return newData;
});

const kpis = computed(() => {
  const newData = leverStore.buildings?.kpis;
  const confKpis = buildingsConfig.kpis;
  const returnData = newData?.map((kpi) => {
    const confKpi = confKpis.find((conf) => conf.name === kpi.title);
    return Object.assign({}, confKpi, kpi);
  });
  console.log('KPI data:', returnData);
  return returnData || [];
});

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
