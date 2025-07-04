<template>
  <q-layout view="hHh lpR fFf">
    <q-page-container>
      <div class="row no-wrap" style="height: 100vh">
        <!-- Left Column -->
        <div class="col-auto" style="width: 400px; border-right: 1px solid #e0e0e0">
          <div class="q-pa-md column full-height">
            <!-- Sector & Levers Header -->
            <div class="non-scrollable-part">
              <div class="text-h5 q-mb-md">Sector</div>
              <q-btn-toggle
                v-model="currentSector"
                :options="[
                  { label: 'Buildings', value: 'buildings' },
                  { label: 'Transport', value: 'transport' },
                  { label: 'Agriculture', value: 'agriculture' },
                  { label: 'Forestry', value: 'forestry'}
                ]"
                toggle-color="primary"
                unelevated
                spread
                class="q-mb-md"
              />

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

            <!-- Scrollable Levers -->
            <q-scroll-area class="col">
              <LeverGroups :sector="currentSector" />
            </q-scroll-area>
          </div>
        </div>

        <!-- Right Column -->
        <div class="col">
          <q-page>
            <kpi-list class="q-pa-md" />
            <router-view />
          </q-page>
        </div>
      </div>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useLeverStore } from 'stores/leversStore';
import { ExamplePathways } from 'utils/examplePathways';
import LeverGroups from 'components/LeverGroups.vue';
import KpiList from 'components/kpi/KpiList.vue';

const leverStore = useLeverStore();
const route = useRoute();
const router = useRouter();

// Sector selection
const currentSector = ref(route.path.split('/')[1] || 'buildings');

watch(currentSector, (newSector) => {
  if (newSector !== route.path.split('/')[1]) {
    void router.push(`/${newSector}`);
  }
});

watch(
  () => route.path,
  (newPath) => {
    const sector = newPath.split('/')[1];
    if (sector && sector !== currentSector.value) {
      currentSector.value = sector;
    }
  },
  { immediate: true },
);

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
/* No custom styles needed for this basic layout */
</style>
