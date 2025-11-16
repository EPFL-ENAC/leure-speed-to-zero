<template>
  <div :class="{ 'kpi-list': true, 'kpi-list-horizontal': horizontal }" ref="kpiListRef">
    <kpi-box v-for="kpi in kpis" :key="getKpiKey(kpi)" v-bind="kpi" :data-route="kpi.route" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import type { KPI } from 'src/utils/sectors';
import KpiBox from './KpiBox.vue';
import { getTranslatedText } from 'src/utils/translationHelpers';
import { useI18n } from 'vue-i18n';

const { locale } = useI18n();
const kpiListRef = ref<HTMLElement | null>(null);
const canScroll = ref(false);

const props = defineProps<{
  kpis: KPI[];
  horizontal?: boolean;
}>();

const emit = defineEmits<{
  canScroll: [value: boolean];
}>();

function getKpiKey(kpi: KPI): string {
  return typeof kpi.name === 'string' ? kpi.name : getTranslatedText(kpi.name, locale.value);
}

function checkScrollability() {
  if (!kpiListRef.value || !props.horizontal) {
    canScroll.value = false;
    emit('canScroll', false);
    return;
  }

  const hasScroll = kpiListRef.value.scrollWidth > kpiListRef.value.clientWidth;
  canScroll.value = hasScroll;
  emit('canScroll', hasScroll);
}

let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
  if (kpiListRef.value) {
    resizeObserver = new ResizeObserver(() => {
      checkScrollability();
    });
    resizeObserver.observe(kpiListRef.value);
    void nextTick(() => checkScrollability());
  }
});

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
});

watch(
  () => props.kpis,
  () => {
    void nextTick(() => checkScrollability());
  },
  { deep: true },
);

defineExpose({
  scrollToRoute: (route: string) => {
    if (!kpiListRef.value) return;
    const kpiElement = kpiListRef.value.querySelector(`[data-route="${route}"]`) as HTMLElement;
    if (kpiElement) {
      kpiElement.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
  },
});
</script>

<style lang="scss" scoped>
.kpi-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.kpi-list-horizontal {
  display: flex;
  flex-direction: row;
  gap: 0.5rem;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: thin;
  scrollbar-color: #888 #f1f1f1;

  &::-webkit-scrollbar {
    height: 0.5rem;
  }

  &::-webkit-scrollbar-track {
    background: #f1f1f1;
  }

  &::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 0.25rem;

    &:hover {
      background: #555;
    }
  }
}
</style>
