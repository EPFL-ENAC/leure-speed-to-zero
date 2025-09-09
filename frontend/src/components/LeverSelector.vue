<template>
  <div class="lever-selector q-py-sm" :class="{ 'lever-disabled': disabled }">
    <div class="col-12 col-md-7 q-pr-sm justify-between row items-center">
      <span class="text-body2 text-weight-light leverTitle">{{ lever.title }}</span>
      <q-chip outline circle size="sm">{{ displayValue }}</q-chip>
    </div>
    <div class="row items-center q-col-gutter-xs">
      <div class="content-center col-grow">
        <div class="custom-slider-container">
          <div class="custom-slider-track">
            <div
              v-for="(area, index) in lever.difficultyColors"
              :key="index"
              class="custom-slider-segment"
              :style="{ flex: area.max - area.min + 1, 'background-color': area.color }"
            ></div>
          </div>
          <q-slider
            :model-value="value"
            :min="1"
            :max="maxValue"
            :step="1"
            :disable="disabled"
            dense
            class="transparent-slider"
            @update:model-value="onChange"
          />
        </div>
      </div>
    </div>
    <div class="row q-mt-xs" v-if="lever.difficultyColors && lever.difficultyColors.length > 0">
      <div class="col-12">
        <div class="difficulty-labels text-caption text-grey-7">
          <span>{{ lever.difficultyColors[0]?.label }}</span>
          <span>{{ lever.difficultyColors[lever.difficultyColors.length - 1]?.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Lever } from 'src/utils/leversData';

const props = defineProps<{
  lever: Lever;
  value: number;
}>();

const emit = defineEmits<{
  change: [value: number];
}>();

const disabled = computed(() => props.lever.disabled || false);

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

// Handle value changes
function onChange(newValue: number | null) {
  if (newValue !== null && !disabled.value) {
    emit('change', newValue);
  }
}
</script>

<style lang="scss" scoped>
.lever-selector {
  padding-bottom: 2rem;

  &.lever-disabled {
    opacity: 0.8;
    cursor: pointer;
    .custom-slider-track {
      filter: grayscale(100%);
    }
  }
}

.custom-slider-container {
  position: relative;
  height: 20px; /* Adjust height as needed */
  display: flex;
  align-items: center;
}

.custom-slider-track {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 100%;
  height: 12px;
  border-radius: 4px;
  display: flex;
  overflow: hidden;
}

.custom-slider-segment {
  height: 100%;
}

.transparent-slider {
  position: absolute;
  width: 100%;
  // Make track transparent
  :deep(.q-slider__track-container) {
    background: transparent;
    color: transparent;
  }
  :deep(.q-slider__track) {
    background: transparent;
    color: transparent;
    height: 0px !important;
  }
  // Adjust thumb color if needed
  :deep(.q-slider__thumb) {
    background-color: rgba(255, 255, 255, 0.664);
    border-radius: 12px;
    color: grey;
  }
}

.difficulty-labels {
  display: flex;
  justify-content: space-between;
  width: 100%;
  padding: 0 2px;
}

.leverTitle {
  text-wrap-mode: nowrap;
  text-overflow: ellipsis;
  overflow: clip;
}
</style>
