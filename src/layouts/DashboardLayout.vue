<template>
  <q-layout view="hHh lpR fFf">
    <!-- Left sidebar for levers -->
    <q-drawer v-model="leftDrawerOpen" show-if-above bordered :width="400" class="lever-sidebar">
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
    </q-drawer>

    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="leftDrawerOpen = !leftDrawerOpen"
        />

        <q-toolbar-title> Speed To Zero </q-toolbar-title>

        <!-- Main tab navigation -->
        <q-tabs dense no-caps align="center" class="q-ml-md">
          <q-route-tab name="buildings" to="/buildings" label="Buildings" />
          <q-route-tab name="transport" to="/transport" label="Transport" />
          <q-route-tab name="test-api" to="/test-api" label="Test API" />
        </q-tabs>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useLeverStore } from 'stores/leversStore';
import { ExamplePathways } from 'utils/examplePathways';
import LeverGroups from 'components/LeverGroups.vue';

const leverStore = useLeverStore();
const leftDrawerOpen = ref(true);

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
}
</style>
