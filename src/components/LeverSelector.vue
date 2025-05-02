<template>
  <div class="lever-selector">
    <div class="text-body2 lever-title">{{ lever.title }}</div>
    <div class="row items-center">
      <q-slider
        :model-value="value"
        :min="0"
        :max="maxValue"
        :step="1"
        dense
        class="individual-slider q-mx-sm"
        @update:model-value="onChange"
      />
      <q-chip outline circle>{{ displayValue }}</q-chip>
    </div>
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
    return props.lever.range[props.value] || props.lever.range[0];
  }
});

const maxValue = computed(() => {
  if (props.lever.type === 'num' && props.lever.range?.length) {
    return Math.max(...props.lever.range.filter((v) => typeof v === 'number'));
  }
  return props.lever.range.length - 1;
});

// Create marker labels for the slider
// const markerLabels = computed(() => {
//   const labels: Record<number, string> = {};

//   if (props.lever.type === 'num') {
//     // For numeric levers, use the number values
//     props.lever.range.forEach((value) => {
//       if (typeof value === 'number') {
//         labels[value] = value.toString();
//       }
//     });
//   } else {
//     // For letter levers, use the letter values at their indices
//     props.lever.range.forEach((value, index) => {
//       labels[index] = value.toString();
//     });
//   }

//   return labels;
// });

// Handle value changes
function onChange(newValue: number | null) {
  if (newValue !== null) emit('change', newValue);
}
</script>

<style lang="scss" scoped>
.lever-selector {
  padding: 6px 12px;
  margin-bottom: 4px;
  gap: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.lever-title {
  font-weight: medium;
  font-size: small;
  // width: 120px;
}

.individual-slider {
  width: 120px;
  padding-right: 1.2rem;
}
</style>
