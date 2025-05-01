<template>
  <div class="lever-selector">
    <div class="row items-center q-mb-sm">
      <div class="col lever-title">{{ lever.title }}</div>
      <div class="col-auto">
        <q-chip dense v-if="lever.type === 'num'">{{ value }}</q-chip>
        <q-chip dense v-else>{{ value }}</q-chip>
      </div>
    </div>

    <!-- Numeric lever slider -->
    <template v-if="lever.type === 'num'">
      <q-slider
        v-model="localValue as number"
        :min="minValue"
        :max="maxValue"
        :step="1"
        markers
        label
        :marker-labels="markerLabels"
        @change="onChange"
      />
    </template>

    <!-- Character lever button group -->
    <template v-else>
      <div class="row q-gutter-sm">
        <q-btn
          v-for="option in lever.range"
          :key="option"
          :label="option"
          :color="value === option ? 'primary' : 'grey-4'"
          :text-color="value === option ? 'white' : 'black'"
          dense
          @click="onChange(option)"
        />
      </div>
    </template>
  </div>
</template>
<script setup lang="ts">
import { computed, ref, watch } from 'vue';

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
  value: number | string;
}>();

const emit = defineEmits<{
  change: [value: number | string];
}>();

// Create a local value for two-way binding
const localValue = ref<number | string>(props.value);

// Watch for prop changes to update local value
watch(
  () => props.value,
  (newValue) => {
    localValue.value = newValue;
  },
);

// Computed properties for numeric levers
const minValue = computed(() => {
  if (props.lever.type === 'num' && props.lever.range?.length) {
    return Math.min(...props.lever.range.filter((v) => typeof v === 'number'));
  }
  return 1;
});

const maxValue = computed(() => {
  if (props.lever.type === 'num' && props.lever.range?.length) {
    return Math.max(...props.lever.range.filter((v) => typeof v === 'number'));
  }
  return 4;
});

// Create marker labels for the slider
const markerLabels = computed(() => {
  if (props.lever.type !== 'num') return {};

  const labels: Record<string | number, string> = {};
  for (const value of props.lever.range) {
    labels[value] = value.toString();
  }
  return labels;
});

// Handle value changes
function onChange(newValue: number | string) {
  emit('change', newValue);
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
