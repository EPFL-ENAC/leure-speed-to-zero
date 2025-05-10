<template>
  <div class="lever-groups">
    <div v-for="(levers, headline) in leversByHeadline" :key="headline" class="q-mb-xl">
      <q-list>
        <div class="text-subtitle1 q-ml-md q-mb-sm">
          {{ headline }}
        </div>
        <q-expansion-item
          v-for="(groupLevers, group) in getGroupedLevers(levers)"
          :key="group"
          expand-separator
          switch-toggle-side
          class="lever-group"
        >
          <template v-slot:header>
            <div class="row items-center full-width q-col-gutter-sm">
              <div class="col-12 col-md-6">
                <div class="text-subtitle3 lever-group-header">{{ group }}</div>
              </div>
              <div class="col-8 col-md-4 content-center">
                <q-slider
                  :model-value="getGroupValue(groupLevers)"
                  :min="minValue"
                  :max="maxValue"
                  :step="1"
                  dense
                  class="q-mr-sm"
                  @update:model-value="(value) => updateGroupLevers(groupLevers, value ?? 0)"
                />
              </div>
              <div class="col-4 col-md-2 flex justify-center content-center">
                <q-chip outline circle class="text-weight-bold" size="sm"
                  >{{ Math.round(getGroupValue(groupLevers)) }}
                </q-chip>
              </div>
            </div>
          </template>
          <q-card>
            <q-card-section>
              <div v-for="lever in groupLevers" :key="lever.code" class="lever-item">
                <LeverSelector
                  :lever="lever"
                  :value="leverStore.getLeverValue(lever.code)"
                  @change="(value) => leverStore.setLeverValue(lever.code, value)"
                />
              </div>
            </q-card-section>
          </q-card>
        </q-expansion-item>
      </q-list>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useLeverStore } from 'stores/leversStore';
import type { Lever } from 'utils/leversData';
import LeverSelector from 'components/LeverSelector.vue';

const leverStore = useLeverStore();

const minValue = 1,
  maxValue = 4;

// Get all levers organized by headline
const leversByHeadline = computed(() => leverStore.leversByHeadline);

function getGroupValue(levers: Lever[]): number {
  return (
    levers.reduce((acc, lever) => acc + leverStore.getLeverValue(lever.code), 0) / levers.length
  );
}

// Group levers by their group property within each headline
function getGroupedLevers(levers: Lever[]): Record<string, Lever[]> {
  const result: Record<string, Lever[]> = {};

  levers.forEach((lever) => {
    if (!result[lever.group]) {
      result[lever.group] = [];
    }
    result[lever.group]?.push(lever);
  });

  return result;
}

function updateGroupLevers(levers: Lever[], value: number): void {
  // Create a batch update object
  const updates: Record<string, number> = {};

  // Collect all lever updates
  levers.forEach((lever) => {
    updates[lever.code] = value;
  });

  // Apply all updates in a single operation
  leverStore.batchUpdateLevers(updates);
}
</script>

<style lang="scss" scoped>
.group-slider {
  width: 100px;
}
.lever-group:deep(.q-item__section--side) {
  padding-right: 4px;
  min-width: auto;
}
</style>
