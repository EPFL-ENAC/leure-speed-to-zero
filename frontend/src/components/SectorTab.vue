<template>
  <div class="sector-tab-container">
    <!-- Main content area -->
    <div class="content-area">
      <!-- KPI bar at top - horizontal with scroll arrows -->
      <div v-if="modelResults && currentTab && currentTab !== 'overview'" class="top-kpis-bar">
        <q-btn
          flat
          dense
          round
          icon="chevron_left"
          @click="scrollKpis('left')"
          class="kpi-nav-btn"
          :disable="!canScrollKpis"
        />
        <div class="kpis-container" ref="kpisContainerRef">
          <kpi-list
            ref="kpiListRef"
            :kpis="kpis"
            :horizontal="true"
            @can-scroll="canScrollKpis = $event"
          />
        </div>
        <q-btn
          flat
          dense
          round
          icon="chevron_right"
          @click="scrollKpis('right')"
          class="kpi-nav-btn"
          :disable="!canScrollKpis"
        />
      </div>

      <empty-state
        v-if="!modelResults"
        :loading="isLoading"
        :message="$t('runModelToSeeData', { sector: sectorDisplayName })"
        :refresh-label="$t('runModel')"
        @refresh="forceRunModel"
      />

      <template v-else>
        <!-- Show KPI Cards when no subtab is selected (overview) -->
        <div v-if="!currentTab || currentTab === 'overview'" class="overview-content">
          <kpi-list :kpis="kpis" />
        </div>

        <!-- Charts content - scrollable (when subtab is selected) -->
        <q-scroll-area class="charts-content">
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
        </q-scroll-area>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useLeverStore, type ChartConfig } from 'stores/leversStore';
import type { KPI, KPIConfig } from 'src/utils/sectors';
import KpiList from 'src/components/kpi/KpiList.vue';
import ChartCard from 'components/graphs/ChartCard.vue';
import EmptyState from 'components/EmptyState.vue';
import { useQuasar } from 'quasar';
import { getTranslatedText } from 'src/utils/translationHelpers';
import type { TranslationObject } from 'src/utils/translationHelpers';
import { useCurrentSector } from 'src/composables/useCurrentSector';

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

// Set current sector for optimized API calls
useCurrentSector(props.sectorName);

const router = useRouter();
const route = useRoute();
const leverStore = useLeverStore();
const kpisContainerRef = ref<HTMLElement | null>(null);
const kpiListRef = ref<InstanceType<typeof KpiList> | null>(null);
const canScrollKpis = ref(false);

// Helper function to get translated subtab title
const getSubtabTitle = (subtab: { title: string | TranslationObject; route: string }): string => {
  return getTranslatedText(subtab.title, locale.value);
};

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

// Watch for tab changes and scroll to active KPI
watch(currentTab, async (newTab) => {
  if (!newTab || newTab === 'overview') return;
  await nextTick();
  kpiListRef.value?.scrollToRoute(newTab);
});

// If no subtab is present in the URL, redirect to first subtab
if (!route.params.subtab && props.config.subtabs[0]?.route) {
  void router.replace({
    name: props.sectorName,
    params: { subtab: props.config.subtabs[0]?.route },
  });
}

// Get model results for this sector
const modelResults = computed(() => {
  return leverStore.getSectorDataWithKpis(props.sectorName);
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
      // Prefer API values when available, fallback to config values
      return {
        ...confKpi, // config provides: name, route, maximize, info, and fallback values
        value: kpi.value, // runtime provides: value
        unit: kpi.unit || confKpi.unit, // prefer runtime unit, fallback to config
        min: kpi.min ?? confKpi.min, // prefer API min, fallback to config
        max: kpi.max ?? confKpi.max, // prefer API max, fallback to config
        // Handle thresholds: API provides warning/danger directly, config has thresholds object
        thresholds: {
          warning: kpi.warning ?? confKpi.thresholds?.warning ?? 0,
          danger: kpi.danger ?? confKpi.thresholds?.danger ?? 0,
        },
      } as KPI;
    })
    .filter((kpi): kpi is KPI => kpi !== null); // Remove null entries and assert type

  return returnData;
});

const isLoading = computed(() => leverStore.isLoading);

// Force re-run the model
async function forceRunModel() {
  try {
    await leverStore.runModel();
  } catch (error) {
    console.error('Error running model:', error);
  }
}

// Scroll KPIs left or right
function scrollKpis(direction: 'left' | 'right') {
  if (!kpiListRef.value) return;
  const container = kpiListRef.value.$el as HTMLElement;
  const scrollAmount = 300;
  container.scrollBy({
    left: direction === 'left' ? -scrollAmount : scrollAmount,
    behavior: 'smooth',
  });
}
</script>

<style lang="scss" scoped>
.sector-tab-container {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  min-height: 0;
  width: 100%;
}

.top-kpis-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0.5rem;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  min-height: 100px;
}

.kpi-nav-btn {
  flex-shrink: 0;
  transition: opacity 0.3s;

  &:disabled,
  &.disabled {
    opacity: 0.3;
    color: #9e9e9e;
  }
}

.kpis-container {
  flex: 1;
  min-width: 0;
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
  :deep(.q-scrollarea__content) {
    padding-top: 2rem;
    width: 100%;
  }
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
