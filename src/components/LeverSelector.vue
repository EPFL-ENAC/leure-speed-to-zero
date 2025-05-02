<template>
  <div class="lever-selector">
    <div class="row items-center q-mb-sm">
      <div class="col lever-title">{{ lever.title }}</div>
      <div class="col-auto">
        <q-chip dense>{{ displayValue }}</q-chip>
      </div>
    </div>

    <!-- Slider for all lever types -->
    <q-slider
      :model-value="value"
      :min="1"
      :max="maxValue"
      :step="1"
      markers
      label
      :label-value="displayValue"
      :marker-labels="markerLabels"
      @update:model-value="onChange"
    />
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue';

// Define the Lever interface
interface Lever {
  code: string;
  title: string;
  type: string;
  range: (string | number)[];
  group: string;
  headline: string;
}

const props = defineProps<{
  lever: Lever;
  value: number;
}>();

const emit = defineEmits<{
  change: [value: number];
}>();

const displayValue = computed(() => {
  if (props.lever.type === 'num') {
    return props.value;
  } else {
    // For letter levers, convert number to letter for display
    return props.lever.range[props.value - 1] || props.lever.range[0];
  }
});

const maxValue = computed(() => {
  if (props.lever.type === 'num' && props.lever.range?.length) {
    return Math.max(...props.lever.range.filter((v) => typeof v === 'number'));
  }
  return props.lever.range.length;
});

// Create marker labels for the slider
const markerLabels = computed(() => {
  const labels: Record<number, string> = {};

  if (props.lever.type === 'num') {
    // For numeric levers, use the number values
    props.lever.range.forEach((value) => {
      if (typeof value === 'number') {
        labels[value] = value.toString();
      }
    });
  } else {
    // For letter levers, use the letter values at their indices
    props.lever.range.forEach((value, index) => {
      labels[index + 1] = value.toString();
    });
  }

  return labels;
});

// Handle value changes
function onChange(newValue: number | null) {
  if (newValue) emit('change', newValue);
}
</script>

<style lang="scss" scoped>
.lever-selector {
  padding: 8px 12px;
  border-radius: 4px;
  background-color: #f8f8f8;
}

.lever-title {
  font-weight: 500;
  font-size: 0.9rem;
}
</style>
