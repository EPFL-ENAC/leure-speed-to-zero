<template>
  <div class="sector-tab-container">
    <!-- Main content area -->
    <div class="content-area">
      <template v-if="modelResults && currentTab && currentTab !== 'overview' && $q.screen.gt.sm">
        <h2 class="page-heading">
          {{ sectorHeading }}
          <template v-if="currentTabConfig">
            <span class="page-heading-sep">·</span>
            <span class="page-heading-sub">{{ getSubtabTitle(currentTabConfig) }}</span>
          </template>
        </h2>
        <subtab-nav-bar :subtabs="config.subtabs" :kpis="kpis" :current-tab="currentTab" />
      </template>

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
        <q-scroll-area ref="chartsScrollRef" class="charts-content">
          <q-tab-panels v-if="$q.screen.gt.sm" v-model="currentTab" animated>
            <q-tab-panel
              v-for="tab in config.subtabs"
              class="q-px-md q-pb-md overflow-hidden"
              :key="tab.route"
              :name="tab.route"
            >
              <div v-if="tab.toggle && getPrimaryCharts(tab).length === 0" class="not-available">
                <div class="view-toggle-bar">
                  <q-btn-toggle
                    v-bind="toggleProps"
                    v-model="currentView"
                    :options="getToggleOptions(tab)"
                  />
                </div>
                {{ $t('notYetAvailable') }}
              </div>
              <div
                v-else
                class="row flex-wrap"
                :style="isSingleChart(tab) ? singleChartStyle : undefined"
              >
                <chart-card
                  v-for="(chartId, i) in getPrimaryCharts(tab)"
                  :chart-config="config.charts[chartId] as ChartConfig"
                  :chart-id="chartId"
                  :sector-name="sectorName"
                  :key="chartId"
                  :model-data="modelResults"
                  :fill="isSingleChart(tab)"
                >
                  <template v-if="tab.toggle && i === 0" #header-actions>
                    <q-btn-toggle
                      v-bind="toggleProps"
                      v-model="currentView"
                      :options="getToggleOptions(tab)"
                    />
                  </template>
                </chart-card>
              </div>
              <template v-if="getMoreInfoCharts(tab).length">
                <div class="more-info-toggle">
                  <q-btn
                    flat
                    dense
                    no-caps
                    :label="showMoreInfo ? $t('lessInfo') : $t('moreInfo')"
                    :icon-right="showMoreInfo ? 'expand_less' : 'expand_more'"
                    @click="showMoreInfo = !showMoreInfo"
                  />
                </div>
                <q-slide-transition>
                  <div v-show="showMoreInfo" class="row flex-wrap">
                    <chart-card
                      v-for="chartId in getMoreInfoCharts(tab)"
                      :chart-config="config.charts[chartId] as ChartConfig"
                      :chart-id="chartId"
                      :sector-name="sectorName"
                      :key="chartId"
                      :model-data="modelResults"
                    />
                  </div>
                </q-slide-transition>
              </template>
            </q-tab-panel>
          </q-tab-panels>

          <!-- Mobile view -->
          <div v-else class="q-pa-md">
            <div v-for="tab in config.subtabs" :key="tab.route" class="mobile-tab-section">
              <div class="mobile-tab-header">
                <div class="text-h6 mobile-tab-title">{{ getSubtabTitle(tab) }}</div>
              </div>
              <div v-if="tab.toggle" class="view-toggle-bar">
                <q-btn-toggle
                  v-model="currentView"
                  :options="getToggleOptions(tab)"
                  dense
                  unelevated
                  no-caps
                  toggle-color="primary"
                  color="white"
                  text-color="primary"
                />
              </div>
              <div v-if="tab.toggle && getPrimaryCharts(tab).length === 0" class="not-available">
                {{ $t('notYetAvailable') }}
              </div>
              <div v-else class="row flex-wrap">
                <chart-card
                  v-for="chartId in getPrimaryCharts(tab)"
                  :chart-config="config.charts[chartId] as ChartConfig"
                  :chart-id="chartId"
                  :sector-name="sectorName"
                  :key="chartId"
                  :model-data="modelResults"
                />
              </div>
              <template v-if="getMoreInfoCharts(tab).length">
                <div class="more-info-toggle">
                  <q-btn
                    flat
                    dense
                    no-caps
                    :label="showMoreInfo ? $t('lessInfo') : $t('moreInfo')"
                    :icon-right="showMoreInfo ? 'expand_less' : 'expand_more'"
                    @click="showMoreInfo = !showMoreInfo"
                  />
                </div>
                <q-slide-transition>
                  <div v-show="showMoreInfo" class="row flex-wrap">
                    <chart-card
                      v-for="chartId in getMoreInfoCharts(tab)"
                      :chart-config="config.charts[chartId] as ChartConfig"
                      :chart-id="chartId"
                      :sector-name="sectorName"
                      :key="chartId"
                      :model-data="modelResults"
                    />
                  </div>
                </q-slide-transition>
              </template>
              <q-separator color="grey-3" class="q-mt-xl"></q-separator>
            </div>
          </div>
        </q-scroll-area>
      </template>
    </div>
    <DisclaimerBanner />
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue';
import type { QScrollArea } from 'quasar';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useLeverStore, type ChartConfig } from 'stores/leversStore';
import type { KPI, KPIConfig } from 'src/utils/sectors';
import KpiList from 'src/components/kpi/KpiList.vue';
import SubtabNavBar from 'src/components/kpi/SubtabNavBar.vue';
import ChartCard from 'components/graphs/ChartCard.vue';
import EmptyState from 'components/EmptyState.vue';
import { useQuasar } from 'quasar';
import { getTranslatedText } from 'src/utils/translationHelpers';
import type { TranslationObject } from 'src/utils/translationHelpers';
import { useCurrentSector } from 'src/composables/useCurrentSector';
import DisclaimerBanner from 'components/DisclaimerBanner.vue';
import { sectors } from 'src/utils/sectors';

const $q = useQuasar();
const { locale } = useI18n();

interface SubtabToggleOption {
  value: string;
  label: string | TranslationObject;
}

interface SubtabConfig {
  title: string | TranslationObject;
  route: string;
  charts?: string[];
  toggle?: {
    default: string;
    options: SubtabToggleOption[];
    charts: Record<string, string[]>;
  };
  moreInfo?: string[] | Record<string, string[]>;
}

interface SectorConfig {
  kpis?: KPIConfig[];
  subtabs: SubtabConfig[];
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

// Helper function to get translated subtab title
const getSubtabTitle = (subtab: { title: string | TranslationObject; route: string }): string => {
  return getTranslatedText(subtab.title, locale.value);
};

// Desktop page heading: translated sector label (the Overall page has an empty sectorName)
const sectorHeading = computed(() => {
  const sectorKey = route.path.split('/')[1] || props.sectorName;
  const sector = sectors.find((s) => s.value === sectorKey);
  return sector ? getTranslatedText(sector.label, locale.value) : props.sectorDisplayName;
});

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

// Toggle state (e.g. passenger/freight, residential/non-residential) for subtabs that declare one
const currentTabConfig = computed(() =>
  props.config.subtabs.find((tab) => tab.route === currentTab.value),
);

const currentView = ref('');
const showMoreInfo = ref(false);

// Initialize/refresh the toggle state from the tab's default, or from a `?view=` deep link (set by KPI clicks)
watch(
  [currentTabConfig, () => route.query.view],
  ([tab, queryView]) => {
    if (!tab?.toggle) {
      currentView.value = '';
      return;
    }
    const validValues = tab.toggle.options.map((o) => o.value);
    const requestedView = typeof queryView === 'string' ? queryView : undefined;
    currentView.value =
      requestedView && validValues.includes(requestedView) ? requestedView : tab.toggle.default;
  },
  { immediate: true },
);

// Collapse the "more info" section whenever the active subtab changes
watch(currentTab, () => {
  showMoreInfo.value = false;
});

const getToggleOptions = (tab: SubtabConfig) =>
  (tab.toggle?.options ?? []).map((option) => ({
    value: option.value,
    label: getTranslatedText(option.label, locale.value),
  }));

const toggleProps = {
  dense: true,
  unelevated: true,
  noCaps: true,
  toggleColor: 'primary',
  color: 'white',
  textColor: 'primary',
} as const;

// A subtab with a single primary chart gets the full available height
const isSingleChart = (tab: SubtabConfig) => getPrimaryCharts(tab).length === 1;

// Measure the visible chart area so a single chart can fill it exactly. A CSS height chain
// doesn't work here: Quasar's scroll area content only has a min-height, so `height: 100%`
// below it never resolves. "More info" charts then sit below the fold and scroll.
const chartsScrollRef = ref<QScrollArea | null>(null);
const chartsAreaHeight = ref(0);
const SINGLE_CHART_MIN_HEIGHT = 420;
const SINGLE_CHART_VERTICAL_PADDING = 24; // scroll content padding-top + panel bottom padding

const singleChartStyle = computed(() => ({
  height: `${Math.max(SINGLE_CHART_MIN_HEIGHT, chartsAreaHeight.value - SINGLE_CHART_VERTICAL_PADDING)}px`,
}));

let chartsAreaObserver: ResizeObserver | null = null;

watch(chartsScrollRef, (scrollArea) => {
  chartsAreaObserver?.disconnect();
  const el = scrollArea?.$el as HTMLElement | undefined;
  if (!el) return;
  chartsAreaObserver = new ResizeObserver(([entry]) => {
    chartsAreaHeight.value = entry?.contentRect.height ?? 0;
  });
  chartsAreaObserver.observe(el);
});

onUnmounted(() => chartsAreaObserver?.disconnect());

const getPrimaryCharts = (tab: SubtabConfig): string[] => {
  if (tab.toggle) {
    return tab.toggle.charts[currentView.value] ?? tab.toggle.charts[tab.toggle.default] ?? [];
  }
  return tab.charts ?? [];
};

const getMoreInfoCharts = (tab: SubtabConfig): string[] => {
  if (!tab.moreInfo) return [];
  if (Array.isArray(tab.moreInfo)) return tab.moreInfo;
  return tab.moreInfo[currentView.value] ?? [];
};

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
</script>

<style lang="scss" scoped>
.sector-tab-container {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  min-height: 0;
  width: 100%;
  padding-top: 0.5rem;
}

.page-heading {
  flex-shrink: 0;
  margin: 0;
  padding: 0.25rem 1.25rem 0.75rem;
  font-size: 1.6rem;
  font-weight: 600;
  line-height: 1.3;
  color: #111827;
}

.page-heading-sep {
  margin: 0 0.5rem;
  color: #9ca3af;
}

.page-heading-sub {
  color: #4b5563;
  font-weight: 500;
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

.charts-content {
  flex: 1;
  :deep(.q-scrollarea__content) {
    padding-top: 0.5rem;
    width: 100%;
  }
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

.view-toggle-bar {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.not-available {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: #9e9e9e;
  font-style: italic;
}

.more-info-toggle {
  display: flex;
  justify-content: center;
  width: 100%;
  margin-top: 0.5rem;
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
