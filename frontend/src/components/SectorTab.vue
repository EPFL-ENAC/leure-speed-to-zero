<template>
  <div class="sector-tab-container">
    <!-- Tab selector bar - sticky at top -->
    <template v-if="$q.screen.gt.sm">
      <div class="tab-selector-bar">
        <q-tabs
          v-model="currentTab"
          :ripple="true"
          outside-arrows
          active-color="primary"
          no-caps
          align="justify"
          content-class="text-grey-8"
          active-bg-color="white"
        >
          <q-tab
            v-for="tab in config.subtabs"
            :key="tab.route"
            :name="tab.route"
            :label="tab.title"
          />
        </q-tabs>
        <q-separator></q-separator>
      </div>
    </template>

    <!-- Main content area - scrollable -->
    <div class="content-area">
      <div v-if="!modelResults" class="graph-placeholder">
        <q-icon name="show_chart" size="4rem" />
        <p>{{ $t('runModelToSeeData', { sector: sectorDisplayName }) }}</p>
        <q-btn
          :label="$t('runModel')"
          color="primary"
          :loading="isLoading"
          @click="runModel"
          class="q-mt-md"
        />
      </div>

      <template v-else>
        <!-- Charts content - scrollable -->
        <div class="charts-content">
          <q-tab-panels v-if="$q.screen.gt.sm" v-model="currentTab" animated>
            <q-tab-panel
              v-for="tab in config.subtabs"
              class="q-pa-md overflow-hidden"
              :key="tab.route"
              :name="tab.route"
            >
              <div class="row flex-wrap">
                <chart-card
                  v-for="chartId in tab.charts"
                  :chart-config="config.charts[chartId] as ChartConfig"
                  :key="chartId"
                  :model-data="modelResults"
                />
              </div>
            </q-tab-panel>
          </q-tab-panels>

          <!-- Mobile view -->
          <div v-else class="q-pa-md">
            <div v-for="tab in config.subtabs" :key="tab.route" class="mobile-tab-section">
              <div class="mobile-tab-header">
                <div class="text-h6 mobile-tab-title">{{ tab.title }}</div>
              </div>
              <div class="row flex-wrap">
                <chart-card
                  v-for="chartId in tab.charts"
                  :chart-config="config.charts[chartId] as ChartConfig"
                  :key="chartId"
                  :model-data="modelResults"
                />
              </div>
              <q-separator class="q-mt-xl"></q-separator>
            </div>
          </div>
          <div class="kpis-section">
            <kpi-list :kpis="kpis" class="kpis-content" />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useLeverStore, type SectorWithKpis, type ChartConfig } from 'stores/leversStore';
import type { KPI, KPIConfig } from 'src/utils/sectors';
import KpiList from 'src/components/kpi/KpiList.vue';
import ChartCard from 'components/graphs/ChartCard.vue';
import { useQuasar } from 'quasar';

const $q = useQuasar();

interface SectorConfig {
  kpis?: KPIConfig[];
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

// Tab state - reactive to route changes
const currentTab = computed({
  get: () => {
    return typeof route.params.subtab === 'string' && route.params.subtab
      ? route.params.subtab
      : props.config.subtabs[0]?.route;
  },
  set: (newTab: string) => {
    if (newTab && newTab !== route.params.subtab) {
      void router.push({
        name: props.sectorName,
        params: { subtab: newTab },
      });
    }
  },
});

// If no subtab is present in the URL, redirect to the default one.
if (!route.params.subtab && props.config.subtabs[0]?.route) {
  void router.replace({
    name: props.sectorName,
    params: { subtab: props.config.subtabs[0]?.route },
  });
}

// Get model results for this sector
const modelResults = computed(() => {
  return leverStore[props.sectorName as keyof typeof leverStore] as SectorWithKpis | null;
});

const kpis = computed((): KPI[] => {
  const newData = modelResults.value?.kpis;
  const confKpis = props.config.kpis || [];

  if (!confKpis || !newData) return [];

  const returnData = newData
    .map((kpi) => {
      const confKpi = confKpis.find((conf) => conf.name === kpi.title);
      if (!confKpi) return null;

      // Merge config with runtime data, ensuring the KPI interface is satisfied
      return {
        ...confKpi, // config provides: name, route, maximize, thresholds, info
        value: kpi.value, // runtime provides: value
        unit: kpi.unit || confKpi.unit, // prefer runtime unit, fallback to config
      } as KPI;
    })
    .filter((kpi): kpi is KPI => kpi !== null); // Remove null entries and assert type

  return returnData;
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
.sector-tab-container {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
}

.tab-selector-bar {
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 10;
}

.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.charts-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-bottom: 200px;
}

.graph-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #f5f5f5;
  border-radius: 8px;
  color: #9e9e9e;
  text-align: center;
  padding: 2rem;
  margin: 1rem;
}

@media screen and (min-width: 600px) {
  .kpis-section {
    flex-shrink: 0;
    position: absolute;
    width: 100%;
    bottom: 0;
    z-index: 5;
  }
}

.kpis-content {
  padding: 1rem;
}

.title {
  padding: 1em 0 0 0;
}

.mobile-tab-section {
  margin-bottom: 5rem;

  &:not(:first-child) {
    margin-top: 3rem;
  }
}

.mobile-tab-header {
  padding: 1rem;
  margin-bottom: 1.5rem;
  position: relative;
  text-align: center;
}

.mobile-tab-title {
  margin: 0;
  color: rgba(0, 0, 0, 0.87);
  font-weight: 500;
  font-size: 1.125rem;
  line-height: 1.4;
  letter-spacing: 0.0125em;
}

:deep(.q-tabs) {
  .q-tab {
    padding: 1em;

    @media (max-width: 600px) {
      padding: 0.8em 0.5em;
      font-size: 0.85rem;
    }
  }
}

:deep(.q-tab-panels) {
  flex: 1;
  min-height: 0;
}

:deep(.q-tab-panel) {
  height: auto;
  min-height: 100%;
  padding: 0;
}
</style>
