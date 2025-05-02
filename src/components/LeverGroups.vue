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
          class="lever-group"
        >
          <template v-slot:header>
            <div class="row items-center full-width justify-between">
              <div class="text-subtitle3 lever-group-header">{{ group }}</div>
              <div class="row items-center">
                <q-slider
                  :model-value="getGroupValue(groupLevers)"
                  :min="minValue"
                  :max="maxValue"
                  :step="1"
                  dense
                  class="group-slider q-mr-sm"
                  @update:model-value="(value) => updateGroupLevers(groupLevers, value ?? 0)"
                />
              </div>
            </div>
          </template>
          <div class="">
            <div v-for="lever in groupLevers" :key="lever.code" class="lever-item q-mb-xs">
              <LeverSelector
                :lever="lever"
                :value="leverStore.getLeverValue(lever.code)"
                @change="(value) => leverStore.setLeverValue(lever.code, value)"
              />
            </div>
          </div>
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

// Update all levers in a group with the same value
function updateGroupLevers(levers: Lever[], value: number): void {
  levers.forEach((lever) => {
    leverStore.setLeverValue(lever.code, value);
  });
}
</script>

<style lang="scss" scoped>
.group-slider {
  width: 100px;
}
</style>
