<template>
  <div
    class="lever-selector q-py-sm"
    :class="{ 'lever-disabled': disabled, 'variant-popup': props.variant === 'popup' }"
  >
    <div class="col-12 col-md-7 q-pr-sm justify-between row items-center">
      <span
        class="text-body2 text-weight-light leverTitle"
        @click="props.variant === 'default' ? openLeverDataPopup() : undefined"
        :title="props.variant === 'default' ? `Click to view ${lever.title} data` : ''"
      >
        {{ lever.title }}
        <q-icon v-if="props.variant === 'default'" name="bar_chart" size="sm" class="q-ml-xs" />
      </span>
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
            :style="{ '--thumb-color': currentThumbColor }"
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

  <!-- Lever Data Popup -->
  <LeverDataPopup ref="leverDataPopupRef" :lever-name="lever.code" />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Lever } from 'src/utils/leversData';
import LeverDataPopup from './LeverDataPopup.vue';

const props = withDefaults(
  defineProps<{
    lever: Lever;
    value: number;
    variant?: 'default' | 'popup';
  }>(),
  {
    variant: 'default',
  },
);

const emit = defineEmits<{
  change: [value: number];
}>();

// Refs
const leverDataPopupRef = ref<InstanceType<typeof LeverDataPopup> | null>(null);

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

// Calculate the current thumb color based on the value position
const currentThumbColor = computed(() => {
  if (!props.lever.difficultyColors || props.lever.difficultyColors.length === 0) {
    return 'rgba(255, 255, 255, 0.664)'; // Default color
  }

  // Find which difficulty color segment the current value falls into
  const currentSegment = props.lever.difficultyColors.find(
    (area) => props.value >= area.min && props.value <= area.max,
  );

  return currentSegment ? currentSegment.color : 'rgba(255, 255, 255, 0.664)';
});

// Handle value changes
function onChange(newValue: number | null) {
  if (newValue !== null && !disabled.value) {
    emit('change', newValue);
  }
}

// Open lever data popup
function openLeverDataPopup() {
  if (!disabled.value && leverDataPopupRef.value) {
    leverDataPopupRef.value.open();
  }
}
</script>

<style lang="scss" scoped>
.lever-selector {
  padding-bottom: 4px;

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
  height: 10px; /* Adjust height as needed */
  display: flex;
  align-items: center;
}

.custom-slider-track {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 100%;
  height: 6px;
  border-radius: 4px;
  display: flex;
  overflow: hidden;

  // Popup variant - thicker track
  .variant-popup & {
    height: 10px;
  }
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
    background-color: rgba(255, 255, 255, 0.5);
    color: grey;
    height: 18px !important;
    width: 18px !important;
    border-radius: 50%;
    // Popup variant - thicker track
    .variant-popup & {
      height: 26px !important;
      width: 26px !important;
    }
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

  // Default variant styles
  .lever-selector:not(.variant-popup) & {
    cursor: pointer;
    transition: color 0.2s ease;

    &:hover {
      color: #1976d2;
      text-decoration: underline;
    }

    .q-icon {
      opacity: 0.7;
      transition: opacity 0.2s ease;

      &:hover {
        opacity: 1;
      }
    }
  }

  // Popup variant styles
  .variant-popup & {
    font-size: x-large;
    line-height: 1.2em;
    padding-bottom: 0.5em;
    font-weight: 300;
    cursor: default;
  }
}
</style>
