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
import { type Threshold, type KPI } from 'src/utils/sectors';

const props = withDefaults(defineProps<KPI>(), {
  maximize: false,
});

const currentThreshold = computed(() => {
  // Sort thresholds by value to find the appropriate threshold
  const sortedThresholds = [...props.thresholds].sort((a, b) => a.value - b.value);
  console.log(props.name, sortedThresholds);
  if (props.maximize) {
    // For maximize: higher values are better
    for (let i = sortedThresholds.length - 1; i >= 0; i--) {
      const threshold = sortedThresholds[i];

      if (threshold && props.value >= threshold.value) {
        return threshold;
      }
    }
    // If below all thresholds, use the lowest threshold color
    return sortedThresholds[0] as Threshold;
  } else {
    // For minimize: lower values are better
    for (let i = 0; i < sortedThresholds.length; i++) {
      const threshold = sortedThresholds[i];
      console.log(threshold?.value, props.value);
      if (threshold && props.value <= threshold.value) {
        return threshold;
      }
    }

    // If above all thresholds, use the highest threshold color
    return sortedThresholds[sortedThresholds.length - 1] as Threshold;
  }
});

const colorName = computed(() => {
  return currentThreshold.value.color || 'green';
});

const statusText = computed(() => {
  return currentThreshold.value.label || '';
});

const statusIcon = computed(() => {
  return currentThreshold.value.icon || 'check_circle';
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
