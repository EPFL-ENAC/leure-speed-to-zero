<template>
  <q-layout view="hHh Lpr lff">
    <!-- Mobile Header with Menu Button -->
    <q-header v-if="$q.screen.lt.md" elevated class="bg-white text-dark">
      <q-toolbar>
        <q-btn flat round dense icon="menu" @click="toggleSectorSelector" />
        <q-toolbar-title class="color-primary text-h6">{{ currentSectorDisplay }}</q-toolbar-title>
        <q-btn flat round dense icon="tune" @click="toggleMobileLevers" />
      </q-toolbar>
    </q-header>

    <!-- Sector Column - Desktop always shown, Mobile controlled by sectorSelectorOpen -->
    <q-drawer
      v-model="sectorSelectorOpen"
      side="left"
      bordered
      :mini="miniState"
      @mouseenter="$q.screen.gt.sm ? (miniState = false) : null"
      @mouseleave="$q.screen.gt.sm ? (miniState = true) : null"
      :breakpoint="$q.screen.sizes.sm"
      :width="$q.screen.lt.sm ? 180 : 200"
      :overlay="$q.screen.lt.md"
    >
      <SectorSelector :mini="miniState" ref="sectorSelector" />
    </q-drawer>

    <!-- Levers Column - Desktop/Tablet always shown, Mobile controlled by leversOpen -->
    <q-drawer
      side="right"
      v-model="leversOpen"
      :overlay="$q.screen.lt.sm"
      :width="300"
      :breakpoint="$q.screen.sizes.sm"
      class="col-auto levers-col"
      style="border-left: 1px solid #e0e0e0"
    >
      <div class="column full-height">
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
            class="q-mb-md app-disabled"
            :disable="true"
          >
            <q-tooltip class="bg-grey-8"> Feature not ready </q-tooltip>
          </q-select>
          <q-btn
            label="Reset to Defaults"
            color="grey"
            outline
            class="full-width q-mb-md"
            @click="resetToDefaults"
          >
          </q-btn>
        </div>
        <q-separator />
        <q-scroll-area visible class="col q-pa-md">
          <LeverGroups :sector="currentSector" />
        </q-scroll-area>
      </div>
    </q-drawer>

    <q-page-container>
      <div class="row" :style="{ height: $q.screen.lt.md ? 'calc(100vh - 50px)' : '100vh' }">
        <!-- Main Content Column -->
        <div class="col right-column">
          <q-page class="column full-height">
            <div class="col full-width">
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
import { sectors } from 'utils/sectors';
import LeverGroups from 'components/LeverGroups.vue';
import SectorSelector from 'components/SectorSelector.vue';
import { useQuasar } from 'quasar';
const $q = useQuasar();

const leverStore = useLeverStore();
const sectorSelector = ref<InstanceType<typeof SectorSelector>>();

// Mobile UI state
const leversOpenState = ref(false);
const sectorSelectorOpen = ref($q.screen.gt.sm); // Start open on desktop, closed on mobile
const miniState = ref(false);

// Get current sector from the SectorSelector component
const currentSector = computed(() => sectorSelector.value?.currentSector || 'buildings');

// Get current sector display name
const currentSectorDisplay = computed(() => {
  const sector = sectors.find((s) => s.value === currentSector.value);
  return sector?.label || 'Dashboard';
});

// Mobile UI methods
function toggleMobileLevers() {
  leversOpenState.value = !leversOpenState.value;
}

const leversOpen = computed({
  get: () => leversOpenState.value || $q.screen.gt.sm,
  set: (value) => {
    leversOpenState.value = value;
  },
});

function toggleSectorSelector() {
  // On mobile, toggle the drawer state
  if ($q.screen.lt.md) {
    sectorSelectorOpen.value = !sectorSelectorOpen.value;
  }
}

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
  overflow-y: auto;
}

// .levers-col {
//   flex: 1 2 300px;
//   min-width: 250px;
//   max-width: 400px;
//   max-height: 100%;
// }

.right-column {
  flex: 6 1 400px;
  max-height: 100%;
}

.responsive-layout {
  transition: all 0.3s ease;
  overflow-x: auto; // Allow horizontal scrolling on mobile if needed
}

// Mobile-specific styles
@media (max-width: 600px) {
  .right-column {
    flex: 1;
  }
}

// Tablet-specific styles
@media (min-width: 601px) and (max-width: 1024px) {
  .levers-col {
    flex: 1 2 250px;
    min-width: 200px;
    max-width: 300px;
  }

  .right-column {
    flex: 2 1 400px;
  }
}

// Ensure drawer is properly sized on mobile
:deep(.q-drawer) {
  @media (max-width: 600px) {
    .q-drawer__content {
      width: 100% !important;
    }
  }
}
</style>
