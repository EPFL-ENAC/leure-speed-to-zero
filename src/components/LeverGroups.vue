<template>
  <div class="lever-groups">
    <div
      v-for="(levers, headline) in leversByHeadline"
      :key="headline"
      class="lever-headline-section"
    >
      <div class="text-subtitle1 bg-primary-1 lever-headline q-pa-md">
        {{ headline }}
      </div>
      <div class="q-pt-md">
        <div
          v-for="(groupLevers, group) in getGroupedLevers(levers)"
          :key="group"
          class="lever-group q-mb-sm"
        >
          <q-expansion-item
            header-class="text-subtitle2 bg-grey-3 q-py-xs lever-group-header"
            :default-opened="false"
          >
            <template v-slot:header>
              <div class="row items-center full-width justify-between">
                <div class="text-subtitle2 lever-group-header">{{ group }}</div>
                <div class="row items-center q-mr-md">
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
            <div class="q-py-sm">
              <div v-for="lever in groupLevers" :key="lever.code" class="lever-item q-mb-xs">
                <LeverSelector
                  :lever="lever"
                  :value="leverStore.getLeverValue(lever.code)"
                  @change="(value) => leverStore.setLeverValue(lever.code, value)"
                />
              </div>
            </div>
          </q-expansion-item>
        </div>
      </div>
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
.lever-headline {
  font-weight: 600;
  background-color: #e6f2ff !important;
  font-size: 0.95rem;
  border-radius: 4px;
}

.lever-group-header {
  font-weight: 500;
  font-size: 0.85rem;
}

.lever-headline-section {
  margin-bottom: 10px;
}

.group-slider {
  width: 100px;
}
</style>
