<template>
  <component
    :is="route ? 'router-link' : 'div'"
    :to="route ? { name: $route.name, params: { ...$route.params, subtab: route } } : undefined"
    class="kpi-box"
    :class="{ active: isActive, clickable: route }"
    :style="boxStyle"
  >
    <div class="header">
      <h4 class="title">{{ translatedName }}</h4>
      <q-icon :name="statusIcon" size="1rem" :color="statusColor" />
    </div>

    <div class="metric">
      <span class="value">{{ formatValue(value) }}</span>
      <span class="unit">{{ unit }}</span>
    </div>

    <div class="scale">
      <div class="bar">
        <div v-for="zone in zoneStyles" :key="zone.name" class="zone" :style="zone.style" />
        <div class="indicator" :style="indicatorStyle" />
      </div>
      <div class="markers">
        <div class="marker" :style="`left: ${warningPosition}%`">
          <div class="line" />
          <span class="label">{{ formatValue(thresholds.warning) }}</span>
        </div>
        <div class="marker" :style="`left: ${dangerPosition}%`">
          <div class="line" />
          <span class="label">{{ formatValue(thresholds.danger) }}</span>
        </div>
      </div>
    </div>

    <q-tooltip v-if="translatedInfo" max-width="15rem">
      {{ translatedInfo }}
    </q-tooltip>
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { type KPI } from 'src/utils/sectors';
import { getTranslatedText } from 'src/utils/translationHelpers';

const { locale } = useI18n();
const $route = useRoute();
const props = withDefaults(defineProps<KPI>(), { maximize: false });

const translatedName = computed(() =>
  typeof props.name === 'string' ? props.name : getTranslatedText(props.name, locale.value),
);

const translatedInfo = computed(() =>
  !props.info
    ? ''
    : typeof props.info === 'string'
      ? props.info
      : getTranslatedText(props.info, locale.value),
);

const isActive = computed(() => props.route && $route.params.subtab === props.route);

const formatValue = (val: number) =>
  val >= 1000 ? val.toFixed(0) : val >= 10 ? val.toFixed(1) : val.toFixed(2);

const currentStatus = computed(() => {
  const { warning, danger } = props.thresholds;
  return props.maximize
    ? props.value >= danger
      ? 'excellent'
      : props.value >= warning
        ? 'warning'
        : 'danger'
    : props.value <= warning
      ? 'excellent'
      : props.value <= danger
        ? 'warning'
        : 'danger';
});

const statusIcon = computed(
  () =>
    ({
      excellent: 'o_check_circle',
      warning: 'r_warning',
      danger: 'o_dangerous',
    })[currentStatus.value] || 'check_circle',
);

const statusColor = computed(
  () =>
    ({
      excellent: 'positive',
      warning: 'warning',
      danger: 'negative',
    })[currentStatus.value],
);

const boxStyle = computed(() => {
  if (!isActive.value) return { borderColor: '#e0e0e0', background: 'white' };
  const colors = {
    excellent: { border: '#10b981', bg: '#f0fdf4' },
    warning: { border: '#f59e0b', bg: '#fffbeb' },
    danger: { border: '#ef4444', bg: '#fef2f2' },
  };
  const c = colors[currentStatus.value];
  return { borderColor: c.border, background: c.bg };
});

const indicatorStyle = computed(() => {
  const colors = { excellent: '#10b981', warning: '#f59e0b', danger: '#ef4444' };
  return {
    left: `${valuePosition.value}%`,
    background: colors[currentStatus.value],
  };
});

const scaleMin = computed(() => props.min ?? 0);
const scaleMax = computed(() =>
  props.max !== undefined
    ? props.max
    : Math.max(props.value, props.thresholds.danger, props.thresholds.warning) * 1.2,
);
const scaleRange = computed(() => scaleMax.value - scaleMin.value);

const normalize = (val: number) => ((val - scaleMin.value) / scaleRange.value) * 100;
const valuePosition = computed(() => Math.min(100, Math.max(0, normalize(props.value))));
const warningPosition = computed(() => normalize(props.thresholds.warning));
const dangerPosition = computed(() => normalize(props.thresholds.danger));

const zoneStyles = computed(() => {
  const zones = props.maximize
    ? [
        { name: 'danger', bg: '#fca5a5', left: 0, width: warningPosition.value },
        {
          name: 'warning',
          bg: '#fcd34d',
          left: warningPosition.value,
          width: dangerPosition.value - warningPosition.value,
        },
        {
          name: 'excellent',
          bg: '#86efac',
          left: dangerPosition.value,
          width: 100 - dangerPosition.value,
        },
      ]
    : [
        { name: 'excellent', bg: '#86efac', left: 0, width: warningPosition.value },
        {
          name: 'warning',
          bg: '#fcd34d',
          left: warningPosition.value,
          width: dangerPosition.value - warningPosition.value,
        },
        {
          name: 'danger',
          bg: '#fca5a5',
          left: dangerPosition.value,
          width: 100 - dangerPosition.value,
        },
      ];

  return zones.map((z) => ({
    name: z.name,
    style: { left: `${z.left}%`, width: `${z.width}%`, background: z.bg },
  }));
});
</script>

<style lang="scss" scoped>
.kpi-box {
  display: flex;
  flex-direction: column;
  padding: 0.375rem;
  border: 0.0625rem solid;
  border-radius: 0.375rem;
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.2s;
  min-width: 8rem;
  flex-grow: 1;
  flex-shrink: 1;
  flex-basis: 9rem;
  max-width: 11rem;

  &.clickable {
    cursor: pointer;
    &:hover {
      box-shadow: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.1);
    }
  }
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.375rem;
  margin-bottom: 0.375rem;
  min-height: 1.75rem;
}

.title {
  font-size: smaller;
  font-weight: normal;
  margin: 0;
  line-height: 1.1;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.metric {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
  margin-bottom: 0.375rem;
}

.value {
  font-size: 0.95rem;
  font-weight: 500;
  line-height: 1;
}

.unit {
  font-size: 0.7rem;
  opacity: 0.7;
}

.scale {
  margin-top: auto;
}

.bar {
  position: relative;
  height: 0.3rem;
  background: #e5e7eb;
  border-radius: 9999px;
  overflow: visible;
}

.zone {
  position: absolute;
  height: 100%;
  transition: all 0.3s;
}

.indicator {
  position: absolute;
  top: 50%;
  width: 0.15rem;
  height: 0.6rem;
  transform: translate(-50%, -50%);
  z-index: 10;
  border-radius: 0.075rem;
  transition: left 0.3s;

  &::before {
    content: '';
    position: absolute;
    top: -0.1rem;
    left: 50%;
    transform: translateX(-50%);
    width: 0.4rem;
    height: 0.4rem;
    border-radius: 50%;
    background: inherit;
  }
}

.markers {
  position: relative;
  height: 0.95rem;
  margin-top: 0.1rem;
}

.marker {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  transform: translateX(-50%);
}

.line {
  width: 0.0625rem;
  height: 0.15rem;
  background: #9ca3af;
}

.label {
  font-size: 0.55rem;
  color: #6b7280;
  white-space: nowrap;
}
</style>
