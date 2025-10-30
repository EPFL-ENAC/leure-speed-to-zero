<template>
  <div class="sector-tab-container">
    <!-- Toolbar row at top - always visible -->
    <template v-if="$q.screen.gt.sm">
      <div class="top-toolbar">
        <q-btn
          v-if="currentTab && currentTab !== 'overview'"
          flat
          dense
          icon="arrow_back"
          :label="$t('backToOverview')"
          @click="goToOverview"
          class="back-button"
        />
        <div class="sector-title">{{ sectorDisplayName }}</div>
      </div>
    </template>

    <!-- KPI bar at top - only show when subtab is selected -->
    <template v-if="$q.screen.gt.sm && currentTab && currentTab !== 'overview' && modelResults">
      <div class="top-kpis-bar">
        <kpi-list :kpis="kpis" :horizontal="true" class="top-kpis-content" />
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
        <!-- Show KPI Cards when no subtab is selected (overview) -->
        <div v-if="!currentTab || currentTab === 'overview'" class="overview-content">
          <kpi-card-list :kpis="kpis" />
        </div>

        <!-- Charts content - scrollable (when subtab is selected) -->
        <div v-else class="charts-content">
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
                  :chart-id="chartId"
                  :sector-name="sectorName"
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
                <div class="text-h6 mobile-tab-title">{{ getSubtabTitle(tab) }}</div>
              </div>
              <div class="row flex-wrap">
                <chart-card
                  v-for="chartId in tab.charts"
                  :chart-config="config.charts[chartId] as ChartConfig"
                  :chart-id="chartId"
                  :sector-name="sectorName"
                  :key="chartId"
                  :model-data="modelResults"
                />
              </div>
              <q-separator class="q-mt-xl"></q-separator>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Tab selector bar - sticky at bottom (only show when subtab is selected) -->
    <template v-if="$q.screen.gt.sm && currentTab && currentTab !== 'overview'">
      <div class="bottom-tab-selector">
        <q-separator></q-separator>
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
            :label="getSubtabTitle(tab)"
          />
        </q-tabs>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useLeverStore, type SectorWithKpis, type ChartConfig } from 'stores/leversStore';
import type { KPI, KPIConfig } from 'src/utils/sectors';
import KpiList from 'src/components/kpi/KpiList.vue';
import KpiCardList from 'src/components/kpi/KpiCardList.vue';
import ChartCard from 'components/graphs/ChartCard.vue';
import { useQuasar } from 'quasar';
import { getTranslatedText } from 'src/utils/translationHelpers';
import type { TranslationObject } from 'src/utils/translationHelpers';

const $q = useQuasar();
const { locale } = useI18n();

interface SectorConfig {
  kpis?: KPIConfig[];
  subtabs: Array<{
    title: string | TranslationObject;
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

// Helper function to get translated subtab title
const getSubtabTitle = (subtab: { title: string | TranslationObject; route: string }): string => {
  return getTranslatedText(subtab.title, locale.value);
};

// Function to navigate back to overview
function goToOverview() {
  void router.push({
    name: props.sectorName,
    params: { subtab: 'overview' },
  });
}

// Tab state - reactive to route changes
const currentTab = computed({
  get: () => {
    const subtab = typeof route.params.subtab === 'string' ? route.params.subtab : '';
    // If no subtab or 'overview', return 'overview'
    return subtab || 'overview';
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

// If no subtab is present in the URL, redirect to overview
if (!route.params.subtab) {
  void router.replace({
    name: props.sectorName,
    params: { subtab: 'overview' },
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
      // Find matching config by comparing backend title with translated name
      const confKpi = confKpis.find((conf) => {
        // Handle both string and TranslationObject types
        const confName =
          typeof conf.name === 'string' ? conf.name : getTranslatedText(conf.name, 'enUS'); // Use English as the canonical matching key
        return confName === kpi.title;
      });

      if (!confKpi) {
        console.warn(`No config found for KPI: ${kpi.title}`);
        return null;
      }

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

.top-toolbar {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  gap: 1rem;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 10;
  background: white;
}

.top-kpis-bar {
  flex-shrink: 0;
  position: sticky;
  top: 47px; /* Height of top-toolbar */
  z-index: 9;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  overflow-x: auto;
  overflow-y: hidden;
}

.top-kpis-content {
  padding: 0.5rem 1rem;
  margin-bottom: 1rem;
}

.bottom-tab-selector {
  flex-shrink: 0;
  position: sticky;
  bottom: 0;
  z-index: 10;
  background: white;
  border-top: 1px solid #e0e0e0;
}

.tab-selector-bar {
  flex-shrink: 0;
  position: sticky;
  top: 0;
  z-index: 10;
  background: white;
}

.toolbar-row {
  display: flex;
  align-items: center;
  padding: 0.5rem;
  gap: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.sector-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  text-align: center;
  text-transform: uppercase;
}

.back-button {
  flex-shrink: 0;
}

.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.overview-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.overview-header {
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 0 0 16px 16px;
  margin-bottom: 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.charts-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-top: 2rem;
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
