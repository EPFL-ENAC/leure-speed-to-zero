<template>
  <div class="pathway-comparison">
    <div v-if="runs.length < total" class="status-block">
      <template v-if="error">
        <q-icon name="error_outline" color="negative" size="2rem" />
        <p>{{ $t('pathwayComparisonFailed') }}</p>
        <p class="text-caption text-grey-7">{{ error }}</p>
        <q-btn
          outline
          color="primary"
          :label="$t('retry')"
          @click="leverStore.ensurePathwayComparison()"
        />
      </template>
      <template v-else>
        <p>{{ $t('comparingPathways', { done: runs.length, total }) }}</p>
        <q-linear-progress :value="runs.length / total" color="primary" class="progress" />
      </template>
    </div>

    <template v-else>
      <p class="note text-grey-8">{{ $t('pathwayComparisonNote') }}</p>

      <q-scroll-area class="charts-content">
        <q-tab-panels v-if="$q.screen.gt.sm" v-model="currentTab" animated>
          <q-tab-panel
            v-for="tab in config.subtabs"
            class="q-pa-md overflow-hidden"
            :key="tab.route"
            :name="tab.route"
          >
            <div class="row flex-wrap">
              <pathway-comparison-chart
                v-for="chartId in tab.charts"
                :key="chartId"
                :chart-config="config.charts[chartId] as PathwayChartConfig"
                :runs="runs"
              />
            </div>
          </q-tab-panel>
        </q-tab-panels>

        <!-- Mobile view -->
        <div v-else class="q-pa-md">
          <div v-for="tab in config.subtabs" :key="tab.route" class="mobile-tab-section">
            <div class="text-h6 mobile-tab-title">{{ getTranslatedText(tab.title, locale) }}</div>
            <div class="row flex-wrap">
              <pathway-comparison-chart
                v-for="chartId in tab.charts"
                :key="chartId"
                :chart-config="config.charts[chartId] as PathwayChartConfig"
                :runs="runs"
              />
            </div>
          </div>
        </div>
      </q-scroll-area>
    </template>
    <DisclaimerBanner />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useLeverStore } from 'stores/leversStore';
import { COMPARISON_PATHWAYS, type PathwayChartConfig } from 'src/utils/pathwayComparison';
import { getTranslatedText, type TranslationObject } from 'src/utils/translationHelpers';
import { useCurrentSector } from 'src/composables/useCurrentSector';
import comparisonConfig from 'config/subtabs/pathway-comparison.json';
import PathwayComparisonChart from 'components/graphs/PathwayComparisonChart.vue';
import DisclaimerBanner from 'components/DisclaimerBanner.vue';

interface ComparisonConfig {
  subtabs: Array<{ title: string | TranslationObject; route: string; charts: string[] }>;
  charts: Record<string, unknown>;
}

const config = comparisonConfig as ComparisonConfig;

// The charts come from seven fixed runs of the model, not from the levers the
// user is moving, so this page needs nothing from the live run. The store keeps
// running it though: pointing it at the cheapest sector keeps that background
// run from computing every module.
useCurrentSector('population');

const { locale } = useI18n();
const route = useRoute();
const router = useRouter();
const leverStore = useLeverStore();

const runs = computed(() => leverStore.pathwayComparison);
const total = COMPARISON_PATHWAYS.length;
const error = computed(() => leverStore.pathwayComparisonError);

onMounted(() => {
  void leverStore.ensurePathwayComparison();
});

const currentTab = computed({
  get: () =>
    typeof route.params.subtab === 'string' && route.params.subtab
      ? route.params.subtab
      : config.subtabs[0]?.route,
  set: (newTab: string) => {
    if (newTab && newTab !== route.params.subtab) {
      void router.push({ name: 'pathway-comparison', params: { subtab: newTab } });
    }
  },
});

// No subtab in the URL: go to the first one
if (!route.params.subtab && config.subtabs[0]?.route) {
  void router.replace({ name: 'pathway-comparison', params: { subtab: config.subtabs[0].route } });
}
</script>

<style lang="scss" scoped>
.pathway-comparison {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  min-height: 0;
  width: 100%;
  padding-top: 0.5rem;
}

.status-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  text-align: center;
}

.progress {
  width: min(320px, 70%);
}

.note {
  flex-shrink: 0;
  margin: 0;
  padding: 0.5rem 1.5rem 0;
  font-size: 0.85rem;
}

.charts-content {
  flex: 1;
  :deep(.q-scrollarea__content) {
    padding-top: 1rem;
    width: 100%;
  }
}

.mobile-tab-section {
  margin-bottom: 3rem;
}

.mobile-tab-title {
  padding: 1rem;
  text-align: center;
  font-weight: 500;
  font-size: 1.125rem;
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
