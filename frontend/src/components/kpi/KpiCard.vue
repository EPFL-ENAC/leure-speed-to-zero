<template>
  <div class="kpi-card-wrapper">
    <component
      :is="route ? 'router-link' : 'div'"
      :to="
        route
          ? {
              name: $route.name,
              params: {
                ...$route.params,
                subtab: route,
              },
            }
          : undefined
      "
      class="kpi-card"
      :class="[statusClass, { 'cursor-pointer': route, compact }]"
      :style="cardStyle"
    >
      <!-- Two Column Layout -->
      <div class="kpi-content">
        <!-- Left Column: Header + Metric -->
        <div class="kpi-left-column">
          <!-- Header -->
          <div class="kpi-header">
            <h3 class="kpi-title">{{ translatedName }}</h3>
            <div class="kpi-status">
              <q-icon :name="statusIcon" :class="`status-icon ${currentStatus}`" />
              <span :class="`status-text ${currentStatus}`">
                {{ $t(`kpi.status.${currentStatus}`) }}
              </span>
            </div>
          </div>

          <!-- Metric Display -->
          <div class="kpi-metric">
            <div class="metric-value">
              <span class="metric-number">{{ formatValue(value) }}</span>
              <span class="metric-unit">{{ unit }}</span>
            </div>
            <div class="metric-direction">
              <q-icon :name="maximize ? 'trending_up' : 'trending_down'" size="1rem" />
              <span>{{ maximize ? $t('kpi.higherIsBetter') : $t('kpi.lowerIsBetter') }}</span>
            </div>
          </div>
        </div>

        <!-- Right Column: Info Text -->
        <div v-if="translatedInfo" class="kpi-right-column">
          <div class="info-text-block">
            {{ translatedInfo }}
          </div>
        </div>
      </div>

      <!-- Visual Scale -->
      <div class="kpi-scale">
        <div class="scale-bar">
          <!-- Zone backgrounds -->
          <div
            v-for="zone in zoneStyles"
            :key="zone.name"
            class="scale-zone"
            :class="`zone-${zone.name}`"
            :style="zone.style"
          ></div>

          <!-- Current value indicator -->
          <div
            class="value-indicator"
            :class="currentStatus"
            :style="`left: ${valuePosition}%`"
          ></div>
        </div>

        <!-- Threshold markers -->
        <div class="threshold-markers">
          <div class="threshold-marker" :style="`left: ${warningPosition}%`">
            <div class="marker-line"></div>
            <span class="marker-label">{{ formatValue(thresholds.warning) }} {{ unit }}</span>
          </div>
          <div class="threshold-marker" :style="`left: ${dangerPosition}%`">
            <div class="marker-line"></div>
            <span class="marker-label">{{ formatValue(thresholds.danger) }} {{ unit }}</span>
          </div>
        </div>
      </div>

      <q-tooltip v-if="route" max-width="250px" anchor="top middle" self="bottom middle">
        <div class="tooltip-text">{{ $t('kpi.clickToViewDetails') }}</div>
      </q-tooltip>
    </component>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { type KPI } from 'src/utils/sectors';
import { getTranslatedText } from 'src/utils/translationHelpers';

const { locale, t: $t } = useI18n();

const props = withDefaults(
  defineProps<
    Omit<KPI, 'title'> & {
      title?: string;
      compact?: boolean;
    }
  >(),
  {
    maximize: false,
    compact: false,
  },
);

const translatedName = computed(() => {
  return typeof props.name === 'string' ? props.name : getTranslatedText(props.name, locale.value);
});

const translatedInfo = computed(() => {
  if (!props.info) return '';
  return typeof props.info === 'string' ? props.info : getTranslatedText(props.info, locale.value);
});

function formatValue(val: number): string {
  if (val >= 1000) {
    return val.toFixed(0);
  } else if (val >= 10) {
    return val.toFixed(1);
  } else {
    return val.toFixed(2);
  }
}

// Status calculation
const currentStatus = computed(() => {
  const { warning, danger } = props.thresholds;

  if (props.maximize) {
    // Higher values are better
    if (props.value >= danger) return 'excellent';
    if (props.value >= warning) return 'warning';
    return 'danger';
  } else {
    // Lower values are better
    if (props.value <= warning) return 'excellent';
    if (props.value <= danger) return 'warning';
    return 'danger';
  }
});

const statusIcon = computed(() => {
  switch (currentStatus.value) {
    case 'excellent':
      return 'o_check_circle';
    case 'warning':
      return 'r_warning';
    case 'danger':
      return 'o_dangerous';
    default:
      return 'check_circle';
  }
});

const statusClass = computed(() => `status-${currentStatus.value}`);

const cardStyle = computed(() => ({}));

// Scale calculations
const scaleMax = computed(() => {
  return Math.max(props.value, props.thresholds.danger, props.thresholds.warning) * 1.2;
});

const valuePosition = computed(() => {
  return Math.min(100, (props.value / scaleMax.value) * 100);
});

const warningPosition = computed(() => {
  return (props.thresholds.warning / scaleMax.value) * 100;
});

const dangerPosition = computed(() => {
  return (props.thresholds.danger / scaleMax.value) * 100;
});

// Zone styles based on maximize flag
const zoneStyles = computed(() => {
  if (props.maximize) {
    // For maximize: danger (0 to warning), warning (warning to danger), excellent (danger to 100)
    return [
      {
        name: 'danger',
        style: {
          left: '0%',
          width: `${warningPosition.value}%`,
        },
      },
      {
        name: 'warning',
        style: {
          left: `${warningPosition.value}%`,
          width: `${dangerPosition.value - warningPosition.value}%`,
        },
      },
      {
        name: 'excellent',
        style: {
          left: `${dangerPosition.value}%`,
          width: `${100 - dangerPosition.value}%`,
        },
      },
    ];
  } else {
    // For minimize: excellent (0 to warning), warning (warning to danger), danger (danger to 100)
    return [
      {
        name: 'excellent',
        style: {
          left: '0%',
          width: `${warningPosition.value}%`,
        },
      },
      {
        name: 'warning',
        style: {
          left: `${warningPosition.value}%`,
          width: `${dangerPosition.value - warningPosition.value}%`,
        },
      },
      {
        name: 'danger',
        style: {
          left: `${dangerPosition.value}%`,
          width: `${100 - dangerPosition.value}%`,
        },
      },
    ];
  }
});
</script>

<style lang="scss" scoped>
.kpi-card-wrapper {
  display: block;
  width: 100%;
}

.kpi-card {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  padding: 16px;
  border-width: 2px;
  border-style: solid;
  border-radius: 12px;
  text-decoration: none;
  color: inherit;
  transition: box-shadow 0.2s ease;

  &.compact {
    padding: 12px;
    border-width: 1px;
    border-radius: 8px;

    .metric-number {
      font-size: 1.5rem;
    }

    .metric-unit {
      font-size: 1rem;
    }
  }

  &.cursor-pointer {
    cursor: pointer;

    &:hover {
      box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
  }

  // Status variants
  &.status-excellent {
    background: #f0fdf4;
    border-color: #10b981;
  }

  &.status-warning {
    background: #fffbeb;
    border-color: #f59e0b;
  }

  &.status-danger {
    background: #fef2f2;
    border-color: #ef4444;
  }
}

/* TWO COLUMN LAYOUT */
.kpi-content {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.kpi-left-column {
  flex: 3 1 200px;
  min-width: 0;
}

.kpi-right-column {
  flex: 2 1 200px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.info-text-block {
  font-size: 0.7rem;
  line-height: 1.4;
  max-width: 20rem;
  color: #5c5f64;
}

/* HEADER */
.kpi-header {
  margin-bottom: 12px;
}

.kpi-title {
  font-size: large;
  color: #111827;
  margin-bottom: 4px;
  line-height: 1.3;
}

.kpi-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-icon {
  font-size: 16px;

  &.excellent {
    color: #059669;
  }

  &.warning {
    color: #d97706;
  }

  &.danger {
    color: #dc2626;
  }
}

.status-text {
  font-size: small;
  font-weight: 400;
  text-transform: capitalize;

  &.excellent {
    color: #047857;
  }

  &.warning {
    color: #b45309;
  }

  &.danger {
    color: #b91c1c;
  }
}

.info-button {
  padding: 8px;
  flex-shrink: 0;

  &:hover {
    background: rgba(0, 0, 0, 0.05);
  }
}

.info-text-inline {
  max-width: 200px;
  font-size: 0.75rem;
  line-height: 1.4;
  color: #6b7280;
  text-align: right;
  flex-shrink: 0;
}

/* METRIC DISPLAY */
.metric-value {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 6px;
}

.metric-number {
  font-size: 2rem;
  font-weight: 700;
  color: #111827;
  line-height: 1;
}

.metric-unit {
  font-size: 1rem;
  font-weight: 400;
  color: #4b5563;
}

.metric-direction {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.875rem;
  color: #6b7280;
}

/* VISUAL SCALE */
.kpi-scale {
  margin-bottom: 6px;
}

.scale-bar {
  position: relative;
  height: 12px;
  background: #e5e7eb;
  border-radius: 9999px;
  overflow: visible;
}

.scale-zone {
  position: absolute;
  height: 100%;
  transition: all 0.3s ease;

  &.zone-excellent {
    background: #86efac;
  }

  &.zone-warning {
    background: #fcd34d;
  }

  &.zone-danger {
    background: #fca5a5;
  }
}

/* Current value indicator */
.value-indicator {
  position: absolute;
  top: 50%;
  width: 4px;
  height: 20px;
  transition: left 0.3s ease;
  transform: translate(-50%, -50%);
  z-index: 10;
  border-radius: 2px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);

  &::before {
    content: '';
    position: absolute;
    top: -4px;
    left: 50%;
    transform: translateX(-50%);
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: inherit;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  }

  &.excellent {
    background: #10b981;
  }

  &.warning {
    background: #f59e0b;
  }

  &.danger {
    background: #ef4444;
  }
}

/* Threshold markers */
.threshold-markers {
  position: relative;
  height: 24px;
  margin-top: 4px;
}

.threshold-marker {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  transform: translateX(-50%);
}

.marker-line {
  width: 1px;
  height: 8px;
  background: #9ca3af;
}

.marker-label {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 4px;
  white-space: nowrap;
}

/* LEGEND */
.kpi-legend {
  display: flex;
  justify-content: space-around;
  margin-top: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.7rem;
  color: #6b7280;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;

  &.dot-excellent {
    background: #10b981;
  }

  &.dot-warning {
    background: #f59e0b;
  }

  &.dot-danger {
    background: #ef4444;
  }
}

/* INFO TEXT (removed old panel styles) */
.tooltip-text {
  font-size: 0.875rem;
  padding: 4px;
}
</style>
