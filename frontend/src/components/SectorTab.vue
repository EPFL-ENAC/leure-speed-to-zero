<template>
  <div>
    <!-- KPI List - only show if KPIs exist -->
    <kpi-list v-if="config.kpis && config.kpis.length > 0" :kpis="kpis" />

    <q-tabs v-model="currentTab" outside-arrows active-color="primary" no-caps align="justify">
      <q-tab v-for="tab in config.subtabs" :key="tab.route" :name="tab.route" :label="tab.title" />
    </q-tabs>

    <div v-if="!modelResults" class="graph-placeholder q-pa-xl">
      <q-icon name="show_chart" size="4rem" />
      <p>Run the model to see {{ sectorDisplayName }} data</p>
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
        <q-tab-panel v-for="tab in config.subtabs" :key="tab.route" :name="tab.route">
          <div class="row q-col-gutter-md flex-wrap">
            <chart-card
              v-for="chartId in tab.charts"
              :chart-config="config.charts[chartId] as ChartConfig"
              :key="chartId"
              :model-data="modelResults"
            />
          </div>
        </q-tab-panel>
      </q-tab-panels>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import {
  useLeverStore,
  type SectorWithKpis,
  type KpiConfig,
  type ChartConfig,
} from 'stores/leversStore';
import KpiList from 'src/components/kpi/KpiList.vue';
import ChartCard from 'components/graphs/ChartCard.vue';

// Props
interface SectorConfig {
  kpis?: KpiConfig[];
  subtabs: Array<{
    title: string;
    route: string;
    charts: string[];
  }>;
  charts: Record<string, ChartConfig>;
}

const props = defineProps<{
  sectorName: string;
  sectorDisplayName: string;
  config: SectorConfig;
}>();

const router = useRouter();
const route = useRoute();
const leverStore = useLeverStore();

// Tab state
const currentTab = ref(
  typeof route.params.subtab === 'string' && route.params.subtab
    ? route.params.subtab
    : props.config.subtabs[0]?.route,
);

// If no subtab is present in the URL, redirect to the default one.
if (!route.params.subtab && props.config.subtabs[0]?.route) {
  void router.replace({
    name: props.sectorName,
    params: { subtab: props.config.subtabs[0]?.route },
  });
}

// Watch for tab changes to update URL
watch(currentTab, async (newTab) => {
  if (newTab && newTab !== route.params.subtab) {
    try {
      await router.push({
        name: props.sectorName,
        params: { subtab: newTab },
      });
    } catch (error) {
      console.error('Navigation error:', error);
    }
  }
});

// Get model results for this sector
const modelResults = computed(() => {
  return leverStore[props.sectorName as keyof typeof leverStore] as SectorWithKpis | null;
});

const kpis = computed(() => {
  const newData = modelResults.value?.kpis;
  const confKpis = props.config.kpis || [];

  if (!confKpis || !newData) return [];
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
