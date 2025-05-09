<template>
  <div class="row lever-selector q-col-gutter-xs q-py-sm">
    <div class="col-12 col-md-7 q-pr-sm">
      <span class="text-body2 text-weight-light">{{ lever.title }}</span>
    </div>
    <div class="col-8 col-md-3 content-center">
      <q-slider
        :model-value="value"
        :min="1"
        :max="maxValue"
        :step="1"
        dense
        color="secondary"
        @update:model-value="onChange"
      />
    </div>
    <div class="col-4 col-md-2 q-pl-xs q-mb-xs flex justify-center content-center">
      <q-chip outline circle size="sm">{{ displayValue }}</q-chip>
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

// Handle value changes
function onChange(newValue: number | null) {
  if (newValue !== null) emit('change', newValue);
}
</script>

<style lang="scss" scoped></style>
