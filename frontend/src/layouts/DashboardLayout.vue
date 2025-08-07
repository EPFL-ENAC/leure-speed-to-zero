<template>
  <q-layout view="hHh lpR fFf">
    <q-page-container>
      <div class="row no-wrap" style="height: 100vh">
        <!-- Sector Column -->
        <SectorSelector ref="sectorSelector" />
        <!-- Left Column -->
        <div class="col-auto" style="width: 400px; border-right: 1px solid #e0e0e0">
          <div class="column full-height">
            <!-- Sector & Levers Header -->
            <div class="non-scrollable-part q-pa-md">
              <div class="text-h5 q-mb-md">Levers</div>
              <q-select
                v-model="selectedPathway"
                :options="pathwayOptions"
                label="Select Pathway"
                outlined
                dense
                emit-value
                map-options
                class="q-mb-md"
              />
              <q-btn
                label="Reset to Defaults"
                color="grey"
                outline
                class="full-width q-mb-md"
                @click="resetToDefaults"
              />
            </div>

            <!-- Separator Line -->
            <q-separator class="q-my-md" />

            <!-- Scrollable Levers -->
            <q-scroll-area visible class="col q-pa-md">
              <LeverGroups :sector="currentSector" />
            </q-scroll-area>
          </div>
        </div>

        <!-- Right Column -->
        <div class="col">
          <q-page class="column full-height">
            <div class="col full-width overflow-scroll">
              <router-view />
            </div>
          </q-page>
        </div>
      </div>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useLeverStore } from 'stores/leversStore';
import { ExamplePathways } from 'utils/examplePathways';
import LeverGroups from 'components/LeverGroups.vue';
import SectorSelector from 'components/SectorSelector.vue';

const leverStore = useLeverStore();
const sectorSelector = ref<InstanceType<typeof SectorSelector>>();

// Get current sector from the SectorSelector component
const currentSector = computed(() => sectorSelector.value?.currentSector || 'buildings');

// Pathway selection
const selectedPathway = computed({
  get: () => leverStore.selectedPathway,
  set: (value) => {
    if (value) {
      leverStore.applyPathway(value);
    }
  },
});

// Create pathway options for dropdown
const pathwayOptions = computed(() => {
  return ExamplePathways.map((pathway) => ({
    label: pathway.title,
    value: pathway.title,
  }));
});

function resetToDefaults() {
  leverStore.resetToDefaults();
}
</script>

<style lang="scss" scoped>
.overflow-scroll {
  // height: 100vh;
  overflow-y: auto;
}
/* No custom styles needed for this basic layout */
</style>
