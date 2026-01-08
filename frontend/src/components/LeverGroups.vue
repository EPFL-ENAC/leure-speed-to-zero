<template>
  <div v-if="currentSector == 'overall'" class="lever-groups">
    <div v-for="(levers, headline) in leverStore.leversByHeadline" :key="headline" class="q-mb-xl">
      <q-list>
        <div class="row items-center q-px-sm q-pt-md q-pb-xs">
          <span class="col text-weight-bold">{{ validateHeadline(headline) }}</span>
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
              <div v-for="lever in groupLevers" :key="lever.code" class="q-mb-sm">
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
  <div v-else class="lever-groups">
    <q-list>
      <div v-for="lever in filteredLevers" :key="lever.code" class="q-mb-sm">
        <LeverSelector
          :lever="lever"
          :value="leverStore.getLeverValue(lever.code)"
          @change="(value) => leverStore.setLeverValue(lever.code, value)"
        />
      </div>
    </q-list>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useLeverStore } from 'stores/leversStore';
import LeverSelector from 'components/LeverSelector.vue';
import type { Lever } from 'utils/leversData';
import { getTranslatedText } from 'src/utils/translationHelpers';

const leverStore = useLeverStore();
const route = useRoute();
const { locale, t } = useI18n();

const minValue = 1,
  maxValue = 4;

// Get current sector from route
const currentSector = computed(() => route.path.split('/')[1] || '');

const filteredLevers = computed(() => leverStore.getLeversForSector(currentSector.value));

function getGroupValue(levers: Lever[]): number {
  return (
    levers.reduce((acc, lever) => acc + leverStore.getLeverValue(lever.code), 0) / levers.length
  );
}

function validateHeadline(headline: string): string {
  return headline || t('lever.uncategorized');
}

// Group levers by their group property within each headline
function getGroupedLevers(levers: Lever[]): Record<string, Lever[]> {
  const result: Record<string, Lever[]> = {};

  levers.forEach((lever) => {
    const groupKey = getTranslatedText(lever.group, locale.value);
    if (!result[groupKey]) {
      result[groupKey] = [];
    }
    result[groupKey]?.push(lever);
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
.lever-group:deep(.q-item__section--side) {
  padding-right: 4px;
  min-width: auto;
}
</style>
