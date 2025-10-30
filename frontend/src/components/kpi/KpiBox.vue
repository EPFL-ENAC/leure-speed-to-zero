<template>
  <div class="kpi-box-wrapper">
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
      class="kpi-box"
      :class="[statusClass, { 'cursor-pointer': route, 'is-active': isActive }]"
    >
      <!-- Header -->
      <div class="kpi-box-header">
        <h4 class="kpi-box-title">{{ translatedName }}</h4>
        <q-icon :name="statusIcon" :class="`status-icon ${currentStatus}`" size="1rem" />
      </div>

      <!-- Metric Display -->
      <div class="kpi-box-metric">
        <span class="metric-number">{{ formatValue(value) }}</span>
        <span class="metric-unit">{{ unit }}</span>
      </div>

      <!-- Mini Scale Bar -->
      <div class="kpi-box-scale">
        <div class="mini-scale-bar">
          <!-- Zone backgrounds -->
          <div
            v-for="zone in zoneStyles"
            :key="zone.name"
            class="mini-scale-zone"
            :class="`zone-${zone.name}`"
            :style="zone.style"
          ></div>
          <!-- Current value indicator -->
          <div
            class="mini-value-indicator"
            :class="currentStatus"
            :style="`left: ${valuePosition}%`"
          ></div>
        </div>
      </div>

      <q-tooltip v-if="translatedInfo" max-width="250px" anchor="top middle" self="bottom middle">
        <div class="tooltip-text">{{ translatedInfo }}</div>
      </q-tooltip>
    </component>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { type KPI } from 'src/utils/sectors';
import { getTranslatedText } from 'src/utils/translationHelpers';

const { locale } = useI18n();
const $route = useRoute();

const props = withDefaults(defineProps<KPI>(), {
  maximize: false,
});

const translatedName = computed(() => {
  return typeof props.name === 'string' ? props.name : getTranslatedText(props.name, locale.value);
});

const translatedInfo = computed(() => {
  if (!props.info) return '';
  return typeof props.info === 'string' ? props.info : getTranslatedText(props.info, locale.value);
});

// Check if this KPI's route matches the current route
const isActive = computed(() => {
  if (!props.route) return false;
  return $route.params.subtab === props.route;
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
.kpi-box-wrapper {
  display: inline-block;
  min-width: 160px;
}

.kpi-box {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 12px;
  border-width: 2px;
  border-style: solid;
  border-radius: 8px;
  text-decoration: none;
  color: inherit;
  background: white;
  transition: box-shadow 0.2s ease;
  min-width: 160px;

  &.cursor-pointer {
    cursor: pointer;

    &:hover {
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
  }

  // Default state - grey border, white background
  border-color: #e0e0e0;
  background: white;

  // Active state - colored border and background based on status
  &.status-excellent.is-active {
    border-color: #10b981;
    background: #f0fdf4;
  }

  &.status-warning.is-active {
    border-color: #f59e0b;
    background: #fffbeb;
  }

  &.status-danger.is-active {
    border-color: #ef4444;
    background: #fef2f2;
  }
}

/* HEADER */
.kpi-box-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.kpi-box-title {
  font-size: small;
  font-weight: normal;
  color: #111827;
  margin: 0;
  line-height: 1.2;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.status-icon {
  flex-shrink: 0;

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

/* METRIC DISPLAY */
.kpi-box-metric {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.metric-number {
  font-size: large;
  font-weight: 500;
  color: #111827;
  line-height: 1;
}

.metric-unit {
  font-size: 0.875rem;
  font-weight: 400;
  color: #4b5563;
}

/* MINI SCALE */
.kpi-box-scale {
  margin-top: auto;
}

.mini-scale-bar {
  position: relative;
  height: 6px;
  background: #e5e7eb;
  border-radius: 9999px;
  overflow: visible;
}

.mini-scale-zone {
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

/* Mini value indicator */
.mini-value-indicator {
  position: absolute;
  top: 50%;
  width: 3px;
  height: 12px;
  transition: left 0.3s ease;
  transform: translate(-50%, -50%);
  z-index: 10;
  border-radius: 1.5px;

  &::before {
    content: '';
    position: absolute;
    top: -2px;
    left: 50%;
    transform: translateX(-50%);
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: inherit;
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

.tooltip-text {
  font-size: 0.875rem;
  padding: 4px;
}
</style>
