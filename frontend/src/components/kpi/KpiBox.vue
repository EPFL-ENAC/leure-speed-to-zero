<template>
  <q-card class="kpi-box" flat bordered>
    <q-card-section>
      <div class="row items-start no-wrap">
        <div class="col">
          <div class="text-caption text-grey-8">{{ name }}</div>
          <div class="text-h6 text-weight-bold">
            {{ value.toFixed(2) }}
            <span class="text-body2 text-weight-light">{{ unit }}</span>
          </div>
        </div>
        <div class="col-auto q-pl-xs">
          <q-icon :name="statusIcon" :style="`color: ${colorName}`" size="2rem" />
        </div>
      </div>
    </q-card-section>
    <q-card-section class="q-pt-none">
      <div class="text-caption" :style="`color: ${colorName}`">{{ statusText }}</div>
    </q-card-section>
    <div class="kpi-bar" :style="`background: ${colorName} `"></div>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { type KPI } from 'src/utils/sectors';

const props = withDefaults(defineProps<KPI>(), {
  maximize: false,
});

const currentStatus = computed(() => {
  const { warning, danger } = props.thresholds;

  if (props.maximize) {
    // For maximize: higher values are better
    // Green if >= warning, Yellow if > danger and < warning, Red if <= danger
    if (props.value >= warning.value) return 'good';
    if (props.value > danger.value) return 'warning';
    return 'danger';
  } else {
    // For minimize: lower values are better
    // Green if <= warning, Yellow if > warning and < danger, Red if >= danger
    if (props.value <= warning.value) return 'good';
    if (props.value < danger.value) return 'warning';
    return 'danger';
  }
});

const colorName = computed(() => {
  switch (currentStatus.value) {
    case 'good':
      return '#4CAF50';
    case 'warning':
      return '#FF9800';
    case 'danger':
      return '#F44336';
    default:
      return '#4CAF50';
  }
});

const statusText = computed(() => {
  switch (currentStatus.value) {
    case 'good':
      return 'All good';
    case 'warning':
      return props.thresholds.warning.label;
    case 'danger':
      return props.thresholds.danger.label;
    default:
      return 'All good';
  }
});

const statusIcon = computed(() => {
  switch (currentStatus.value) {
    case 'good':
      return 'check_circle';
    case 'warning':
      return 'warning';
    case 'danger':
      return 'dangerous';
    default:
      return 'check_circle';
  }
});
</script>

<style lang="scss" scoped>
.kpi-box {
  min-width: 180px;
  position: relative;
  overflow: hidden;
  height: 100%;
}
.kpi-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
}
</style>
