<template>
  <div class="lever-groups">
    <div
      v-for="(levers, headline) in leversByHeadline"
      :key="headline"
      class="lever-headline-section"
    >
      <q-expansion-item
        :label="headline"
        header-class="text-subtitle1 bg-primary-1 lever-headline"
        expand-icon-class="lever-headline-icon"
        :default-opened="false"
      >
        <div class="q-pt-md">
          <div
            v-for="(groupLevers, group) in getGroupedLevers(levers)"
            :key="group"
            class="lever-group q-mb-sm"
          >
            <q-expansion-item
              :label="group"
              header-class="text-subtitle2 bg-grey-3 q-py-xs q-pl-sm lever-group-header"
              :default-opened="false"
            >
              <div class="q-py-sm">
                <div v-for="lever in groupLevers" :key="lever.code" class="lever-item q-mb-xs">
                  <LeverSelector
                    :lever="lever"
                    :value="getLeverValue(lever.code)"
                    @change="(value) => setLeverValue(lever.code, value)"
                  />
                </div>
              </div>
            </q-expansion-item>
          </div>
        </div>
      </q-expansion-item>
    </div>
  </div>
</template>

<script setup lang="ts">
// Same script as before
import { computed } from 'vue';
import { useLeverStore } from 'stores/leversStore';
import LeverSelector from 'components/LeverSelector.vue';

const leverStore = useLeverStore();

// Get all levers organized by headline
const leversByHeadline = computed(() => leverStore.leversByHeadline);

// Define the Lever interface to match your data structure
interface Lever {
  code: string;
  title: string;
  group: string;
  headline: string;
  range: (string | number)[];
  type: string;
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

// Methods to interact with the store
function getLeverValue(leverCode: string) {
  return leverStore.getLeverValue(leverCode);
}

function setLeverValue(leverCode: string, value: number | string) {
  leverStore.setLeverValue(leverCode, value);
}
</script>

<style lang="scss" scoped>
.lever-headline {
  font-weight: 600;
  background-color: #e6f2ff !important;
  font-size: 0.95rem;
}

.lever-group-header {
  font-weight: 500;
  font-size: 0.85rem;
}

.lever-headline-section {
  margin-bottom: 10px;
}
</style>
