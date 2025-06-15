<template>
  <q-card class="kpi-box" flat bordered>
    <q-card-section>
      <div class="row items-center no-wrap">
        <div class="col">
          <div class="text-caption text-grey-8">{{ title }}</div>
          <div class="text-h6 text-weight-bold">
            {{ value.toFixed(0) }}
            <span class="text-body2 text-weight-light">{{ unit }}</span>
          </div>
        </div>
        <div class="col-auto">
          <q-icon :name="statusIcon" :color="colorName" size="2rem" />
        </div>
      </div>
    </q-card-section>
    <q-card-section class="q-pt-none">
      <div class="text-caption" :class="`text-${colorName}`">{{ statusText }}</div>
    </q-card-section>
    <div class="kpi-bar" :style="{ backgroundColor: colorHex }"></div>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { colors } from 'quasar';

const props = withDefaults(
  defineProps<{
    title: string;
    value: number;
    unit: string;
    // For things to minimize.
    thresholds: {
      warn: number;
      danger: number;
    };
    // For things to maximize
    maximize?: boolean;
  }>(),
  {
    maximize: false,
  },
);

const colorName = computed(() => {
  if (props.maximize) {
    if (props.value >= props.thresholds.danger) return 'positive';
    if (props.value >= props.thresholds.warn) return 'warning';
    return 'negative';
  } else {
    if (props.value > props.thresholds.danger) return 'negative';
    if (props.value > props.thresholds.warn) return 'warning';
    return 'positive';
  }
});

const colorHex = computed(() => {
  return colors.getPaletteColor(colorName.value);
});

const statusText = computed(() => {
  if (colorName.value === 'positive') return 'Objective met';
  if (colorName.value === 'warning') return 'Approaching limit';
  return 'Limit exceeded';
});

const statusIcon = computed(() => {
  if (colorName.value === 'positive') return 'check_circle';
  if (colorName.value === 'warning') return 'warning';
  return 'error';
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
