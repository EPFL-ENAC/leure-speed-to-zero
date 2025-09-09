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
      class="kpi-circle"
      :class="{ 'cursor-pointer': route }"
      @click="handleClick"
    >
      <div class="kpi-circle-content">
        <div class="kpi-value">
          {{ value.toFixed(1) }}<span class="kpi-unit">{{ unit }}</span>
        </div>
      </div>
      <div class="kpi-name">{{ name }}</div>
      <div class="kpi-status-ring" :style="`border-color: ${colorName}`"></div>
      <q-icon
        :name="statusIcon"
        :style="`color: ${colorName}`"
        class="kpi-status-icon"
        :class="{ rotating: isRotating }"
        size="1.2rem"
      />
      <q-tooltip v-if="info" max-width="250px" anchor="top middle" self="bottom middle">
        <div class="tooltip-text">{{ info }}</div>
      </q-tooltip>
    </component>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { type KPI } from 'src/utils/sectors';

const props = withDefaults(defineProps<KPI>(), {
  maximize: false,
});

const isRotating = ref(false);

function handleClick() {
  if (props.route) {
    // Trigger rotation animation
    isRotating.value = true;

    // Reset animation after it completes
    setTimeout(() => {
      isRotating.value = false;
    }, 600); // Match the animation duration
  }
}

const currentStatus = computed(() => {
  const { warning, danger } = props.thresholds;

  if (props.maximize) {
    // For maximize: higher values are better
    // Green if >= warning, Yellow if > danger and < warning, Red if <= danger
    if (props.value >= warning) return 'good';
    if (props.value > danger) return 'warning';
    return 'danger';
  } else {
    // For minimize: lower values are better
    // Green if <= warning, Yellow if > warning and < danger, Red if >= danger
    if (props.value <= warning) return 'good';
    if (props.value < danger) return 'warning';
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
.kpi-box-wrapper {
  display: block;
  height: 100%;
  min-height: 140px;
}

.kpi-circle {
  position: relative;
  width: 140px;
  height: 140px;
  margin: 0 auto 8px;
  gap: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 3px solid #e0e0e0;
  text-decoration: none;
  color: inherit;
  &:hover {
    background: rgba(0, 0, 0, 0.05);
  }

  &.cursor-pointer {
    cursor: pointer;
  }
}

.kpi-circle-content {
  text-align: center;
  z-index: 2;
}

.kpi-value {
  font-size: x-large;
  font-weight: bold;
  line-height: 1;
}

.kpi-unit {
  font-size: small;
  font-weight: normal;
  margin-left: 4px;
}

.kpi-name {
  font-size: small;
  color: var(--q-dark);
  text-align: center;
  line-height: 1.2;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.kpi-status-ring {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 50%;
  border: 4px solid;
  pointer-events: none;
  transition: all 0.2s ease-in-out;
}

.kpi-status-icon {
  position: absolute;
  top: 8px;
  right: 8px;
  background: white;
  border-radius: 50%;
  padding: 4px;
  border: 1px solid;
  transition: transform 0.4s ease-in-out;

  &.rotating {
    animation: rotateAroundCircle 0.4s ease-in-out;
  }
}

@keyframes rotateAroundCircle {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.tooltip-text {
  font-size: medium;
  padding: 4px;
}
</style>
