<template>
  <div class="calibration">
    <div v-if="!modules" class="status-block">
      <template v-if="error">
        <q-icon name="error_outline" color="negative" size="2rem" />
        <p>{{ $t('calibrationFailed') }}</p>
        <p class="text-caption text-grey-7">{{ error }}</p>
        <q-btn outline color="primary" :label="$t('retry')" @click="load()" />
      </template>
      <q-spinner v-else color="primary" size="2rem" />
    </div>

    <template v-else>
      <p class="note text-grey-8">{{ $t('calibrationNote') }}</p>

      <q-scroll-area class="charts-content">
        <q-tab-panels v-if="$q.screen.gt.sm" v-model="currentTab" animated>
          <q-tab-panel
            v-for="tab in config.subtabs"
            class="q-pa-md overflow-hidden"
            :key="tab.route"
            :name="tab.route"
          >
            <div class="row flex-wrap">
              <calibration-chart
                v-for="calibration in calibrationsOf(tab)"
                :key="calibration.id"
                :calibration="calibration"
                :title="titleOf(calibration)"
              />
            </div>
          </q-tab-panel>
        </q-tab-panels>

        <!-- Mobile view -->
        <div v-else class="q-pa-md">
          <div v-for="tab in config.subtabs" :key="tab.route" class="mobile-tab-section">
            <div class="text-h6 mobile-tab-title">{{ getTranslatedText(tab.title, locale) }}</div>
            <div class="row flex-wrap">
              <calibration-chart
                v-for="calibration in calibrationsOf(tab)"
                :key="calibration.id"
                :calibration="calibration"
                :title="titleOf(calibration)"
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
import { onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { getTranslatedText, type TranslationObject } from 'src/utils/translationHelpers';
import { useCurrentSector } from 'src/composables/useCurrentSector';
import { useCalibrationRates, type Calibration } from 'src/composables/useCalibrationRates';
import calibrationConfig from 'config/subtabs/calibration.json';
import CalibrationChart from 'components/graphs/CalibrationChart.vue';
import DisclaimerBanner from 'components/DisclaimerBanner.vue';

interface CalibrationSubtab {
  title: string | TranslationObject;
  route: string;
  module: string;
  charts: string[];
}

interface CalibrationConfig {
  subtabs: CalibrationSubtab[];
  charts: Record<string, TranslationObject>;
}

const config = calibrationConfig as CalibrationConfig;

// The rates come from their own model run, not from the levers the user is
// moving. Point the store's background run at the cheapest sector.
useCurrentSector('population');

const { locale } = useI18n();
const route = useRoute();
const router = useRouter();
const { modules, error, load } = useCalibrationRates();

onMounted(() => {
  void load();
});

// The calibrations the config lists, in its order, then any the model has
// added since, so a new calibration shows up without editing the config
function calibrationsOf(tab: CalibrationSubtab): Calibration[] {
  const all = modules.value?.[tab.module] ?? [];
  const listed = tab.charts
    .map((id) => all.find((c) => c.id === id))
    .filter((c): c is Calibration => c !== undefined);
  return [...listed, ...all.filter((c) => !tab.charts.includes(c.id))];
}

function titleOf(calibration: Calibration): string {
  const title = config.charts[calibration.id];
  return title ? getTranslatedText(title, locale.value) : calibration.variable;
}

const currentTab = computed({
  get: () =>
    typeof route.params.subtab === 'string' && route.params.subtab
      ? route.params.subtab
      : config.subtabs[0]?.route,
  set: (newTab: string) => {
    if (newTab && newTab !== route.params.subtab) {
      void router.push({ name: 'calibration', params: { subtab: newTab } });
    }
  },
});

// No subtab in the URL: go to the first one
if (!route.params.subtab && config.subtabs[0]?.route) {
  void router.replace({ name: 'calibration', params: { subtab: config.subtabs[0].route } });
}
</script>

<style lang="scss" scoped>
.calibration {
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
