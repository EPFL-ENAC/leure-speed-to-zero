<template>
  <div class="top-kpis-bar">
    <q-btn
      v-if="canScroll"
      flat
      dense
      round
      icon="chevron_left"
      class="nav-btn"
      @click="scrollBy(-300)"
    />
    <div ref="trackRef" class="tabs-track">
      <router-link
        v-for="tab in tabs"
        :key="tab.route"
        :to="{ name: $route.name, params: { ...$route.params, subtab: tab.route } }"
        :data-route="tab.route"
        class="subtab"
        :class="{ active: tab.route === currentTab }"
      >
        <div class="subtab-header">
          <span class="subtab-title">{{ tab.title }}</span>
          <q-icon name="chevron_right" size="1.1rem" class="subtab-chevron" />
        </div>
        <kpi-box v-for="kpi in tab.kpis" :key="kpiKey(kpi)" v-bind="kpi" :route="''" compact />
      </router-link>
      <div v-for="kpi in orphanKpis" :key="kpiKey(kpi)" class="subtab orphan">
        <kpi-box v-bind="kpi" :route="''" compact />
      </div>
    </div>
    <q-btn
      v-if="canScroll"
      flat
      dense
      round
      icon="chevron_right"
      class="nav-btn"
      @click="scrollBy(300)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import type { KPI } from 'src/utils/sectors';
import { getTranslatedText, type TranslationObject } from 'src/utils/translationHelpers';
import KpiBox from './KpiBox.vue';

const props = defineProps<{
  subtabs: { title: string | TranslationObject; route: string }[];
  kpis: KPI[];
  currentTab: string | undefined;
}>();

const { locale } = useI18n();
const trackRef = ref<HTMLElement | null>(null);
const canScroll = ref(false);

const kpiKey = (kpi: KPI) => getTranslatedText(kpi.name, 'enUS');

// One tab per subtab (in config order), each carrying the KPIs that point to it
const tabs = computed(() =>
  props.subtabs.map((subtab) => ({
    route: subtab.route,
    title: getTranslatedText(subtab.title, locale.value),
    kpis: props.kpis.filter((kpi) => kpi.route === subtab.route),
  })),
);

// KPIs whose route matches no subtab are still shown, just not as navigation
const orphanKpis = computed(() => {
  const routes = new Set(props.subtabs.map((s) => s.route));
  return props.kpis.filter((kpi) => !routes.has(kpi.route));
});

function checkScrollability() {
  const el = trackRef.value;
  canScroll.value = !!el && el.scrollWidth > el.clientWidth;
}

function scrollBy(amount: number) {
  trackRef.value?.scrollBy({ left: amount, behavior: 'smooth' });
}

function scrollToActive() {
  const el = trackRef.value?.querySelector(`[data-route="${props.currentTab}"]`);
  el?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
}

let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
  if (trackRef.value) {
    resizeObserver = new ResizeObserver(checkScrollability);
    resizeObserver.observe(trackRef.value);
  }
  void nextTick(() => {
    checkScrollability();
    scrollToActive();
  });
});

onUnmounted(() => resizeObserver?.disconnect());

watch(
  () => props.currentTab,
  () => void nextTick(scrollToActive),
);
watch(tabs, () => void nextTick(checkScrollability), { deep: true });
</script>

<style lang="scss" scoped>
.top-kpis-bar {
  flex-shrink: 0;
  display: flex;
  align-items: stretch;
  gap: 0.25rem;
  padding: 0 1rem 0.75rem;
  background: white;
}

.nav-btn {
  flex-shrink: 0;
  align-self: center;
}

.tabs-track {
  flex: 1;
  min-width: 0;
  display: flex;
  gap: 0.75rem;
  overflow-x: auto;
  scrollbar-width: none;

  &::-webkit-scrollbar {
    display: none;
  }
}

.subtab {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1 0 13rem;
  max-width: 22rem;
  padding: 0.75rem 1rem;
  border: 1px solid #e5e7eb;
  border-top: 3px solid #e5e7eb;
  border-radius: 0.5rem;
  background: white;
  color: inherit;
  text-decoration: none;
  cursor: pointer;
  transition:
    box-shadow 0.15s,
    border-color 0.15s,
    background 0.15s,
    transform 0.15s;

  &:hover {
    box-shadow: 0 0.25rem 0.75rem rgba(0, 0, 0, 0.08);
    transform: translateY(-1px);
    border-top-color: color-mix(in srgb, var(--q-primary) 50%, white);

    .subtab-chevron {
      opacity: 1;
      transform: translateX(0);
    }
  }

  &.active {
    border-top-color: var(--q-primary);
    background: color-mix(in srgb, var(--q-primary) 6%, white);

    .subtab-title {
      color: var(--q-primary);
    }
  }

  &.orphan {
    cursor: default;

    &:hover {
      box-shadow: none;
      transform: none;
    }
  }
}

.subtab-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.subtab-title {
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subtab-chevron {
  opacity: 0;
  transform: translateX(-4px);
  transition:
    opacity 0.15s,
    transform 0.15s;
  color: #6b7280;
}

.subtab.active .subtab-chevron {
  display: none;
}
</style>
