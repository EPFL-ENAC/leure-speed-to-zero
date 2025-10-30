<template>
  <div v-if="kpis.length > 0" class="kpi-card-list" :class="{ compact }">
    <div class="kpi-grid">
      <div v-for="(kpi, index) in kpis" :key="`${kpi.route}-${index}`" class="kpi-grid-item">
        <KpiCard v-bind="kpi" :compact="isCompact" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import KpiCard from './KpiCard.vue';
import { type KPI } from 'src/utils/sectors';

const props = withDefaults(
  defineProps<{
    kpis: KPI[];
    compact?: boolean;
  }>(),
  {
    compact: false,
  },
);

// Ensure compact is always a boolean, never undefined
const isCompact = computed(() => props.compact ?? false);
</script>

<style lang="scss" scoped>
.kpi-card-list {
  width: 100%;
  padding: 1rem;

  &.compact {
    padding: 0.75rem;
  }
}

.kpi-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: 1fr;

  // Full cards - 1 column on mobile, 2 columns on larger screens
  @media (min-width: 1280px) {
    grid-template-columns: repeat(2, 1fr);
  }

  // Compact cards - 1 column on mobile, more columns on larger screens
  .compact & {
    gap: 1rem;

    @media (min-width: 1024px) {
      grid-template-columns: repeat(2, 1fr);
    }

    @media (min-width: 1280px) {
      grid-template-columns: repeat(3, 1fr);
    }
  }
}

.kpi-grid-item {
  display: flex;
}
</style>
