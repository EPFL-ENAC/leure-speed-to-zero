<template>
  <q-page class="row">
    <!-- Left sidebar for levers -->
    <div class="col-3 lever-sidebar">
      <q-scroll-area style="height: 100%">
        <div class="q-pa-md">
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

          <LeverGroups />
        </div>
      </q-scroll-area>
    </div>

    <!-- Main content area with tabs -->
    <div class="col-9 main-content">
      <div class="q-pa-md">
        <!-- Tab navigation -->
        <q-tabs
          v-model="activeTab"
          dense
          class="text-grey"
          active-color="primary"
          indicator-color="primary"
          align="left"
          narrow-indicator
        >
          <q-tab name="emissions" label="Emissions" />
          <q-tab name="energy" label="Energy" />
          <q-tab name="test-api" label="Test API" />
        </q-tabs>

        <q-separator />

        <!-- Tab content panels -->
        <q-tab-panels v-model="activeTab" animated>
          <!-- Emissions Graph Tab -->
          <q-tab-panel name="emissions">
            <EmissionsGraph />
          </q-tab-panel>

          <!-- Energy Graph Tab -->
          <q-tab-panel name="energy">
            <EnergyGraph />
          </q-tab-panel>

          <!-- Test API Tab -->
          <q-tab-panel name="test-api">
            <ApiTester />
          </q-tab-panel>
        </q-tab-panels>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useLeverStore } from 'stores/leversStore';
import { ExamplePathways } from 'utils/examplePathways';
import LeverGroups from 'components/LeverGroups.vue';
import EmissionsGraph from 'components/graphs/EmissionsGraph.vue';
import EnergyGraph from 'components/graphs/EnergyGraph.vue';
import ApiTester from 'components/graphs/ApiTester.vue';

const leverStore = useLeverStore();
const activeTab = ref('emissions'); // Default tab

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
.lever-sidebar {
  border-right: 1px solid #e0e0e0;
  height: calc(100vh - 50px);
}

.main-content {
  height: calc(100vh - 50px);
  overflow-y: auto;
}
</style>
