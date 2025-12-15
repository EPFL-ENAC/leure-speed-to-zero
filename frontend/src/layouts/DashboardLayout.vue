<template>
  <q-layout view="hHh Lpr lff">
    <!-- Mobile Header with Menu Button -->
    <q-header v-if="$q.screen.lt.md" elevated class="bg-white text-dark">
      <q-toolbar>
        <q-btn flat round dense icon="menu" @click="toggleNavigation" />
        <q-toolbar-title class="color-primary text-h6">{{
          getTranslatedText(currentSectorDisplay, $i18n.locale)
        }}</q-toolbar-title>
        <q-btn flat round dense icon="tune" @click="toggleMobileLevers" />
      </q-toolbar>
    </q-header>

    <!-- Vertical Navigation Sidebar -->
    <q-drawer
      v-model="navigationOpen"
      side="left"
      bordered
      :behavior="$q.screen.lt.md ? 'mobile' : 'desktop'"
      :width="miniMode ? 60 : 240"
      class="vertical-nav-drawer"
    >
      <VerticalNavigation :mini="miniMode" @toggle="toggleMiniMode" />
    </q-drawer>

    <!-- Levers Column -->
    <q-drawer
      v-model="leversOpen"
      side="right"
      bordered
      :behavior="$q.screen.lt.md ? 'mobile' : 'desktop'"
      class="levers-col"
      style="border-left: 1px solid #e0e0e0"
    >
      <div class="column full-height">
        <LeversColumnHeader />
        <q-scroll-area visible class="col align-center q-pa-md">
          <q-select
            v-model="selectedPathway"
            :options="pathwayOptions"
            :label="$t('selectPathway')"
            outlined
            dense
            emit-value
            map-options
            class="q-mb-md"
          >
            <q-tooltip class="bg-grey-8">{{ $t('featureNotReady') }}</q-tooltip>
          </q-select>
          <q-btn
            :label="$t('resetDefault')"
            color="grey"
            outline
            class="q-mb-md full-width"
            @click="resetToDefaults"
          />
          <LeverGroups :sector="currentSector" />
        </q-scroll-area>
      </div>
    </q-drawer>

    <q-page-container>
      <div class="row full-height">
        <div class="col right-column">
          <q-page class="column full-height">
            <router-view />
          </q-page>
        </div>
      </div>
    </q-page-container>

    <WelcomePopup />
  </q-layout>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue';
import { useLeverStore } from 'stores/leversStore';
import { ExamplePathways } from 'utils/examplePathways';
import { sectors } from 'utils/sectors';
import LeverGroups from 'components/LeverGroups.vue';
import LeversColumnHeader from 'src/components/LeversColumnHeader.vue';
import VerticalNavigation from 'components/VerticalNavigation.vue';
import WelcomePopup from 'components/WelcomePopup.vue';
import { useQuasar } from 'quasar';
import { useRoute } from 'vue-router';
import { getTranslatedText } from 'src/utils/translationHelpers';
import { useI18n } from 'vue-i18n';
import { useTour } from 'src/composables/useTour';

const $q = useQuasar();
const route = useRoute();
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const { locale } = useI18n();
const leverStore = useLeverStore();
const { startTour } = useTour();

onMounted(() => {
  // Small delay to ensure all elements are rendered
  setTimeout(() => {
    startTour();
  }, 500);
});

// Navigation tab state
const currentTab = ref(route.name as string);
watch(
  () => route.name,
  (newName) => {
    if (newName) currentTab.value = newName as string;
  },
);

// Drawer state - controlled by Quasar breakpoint, manual toggle only for mobile
const miniMode = ref(false);
const navigationOpen = ref($q.screen.gt.sm);
const leversOpen = ref($q.screen.gt.sm);

// Get current sector from route
const currentSector = computed(() => route.path.split('/')[1] || 'buildings');

// Get current sector display name
const currentSectorDisplay = computed(() => {
  const sector = sectors.find((s) => s.value === currentSector.value);
  return sector?.label || 'Dashboard';
});

// Mobile toggle methods
function toggleMobileLevers() {
  leversOpen.value = !leversOpen.value;
}

function toggleNavigation() {
  navigationOpen.value = !navigationOpen.value;
}

function toggleMiniMode() {
  miniMode.value = !miniMode.value;
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

watch(
  () => $q.screen.lt.md,
  (mobileMode) => {
    if (mobileMode) {
      navigationOpen.value = false;
      leversOpen.value = false;
      miniMode.value = false;
    } else {
      leversOpen.value = true;
      navigationOpen.value = true;
      miniMode.value = false;
    }
  },
);
</script>

<style lang="scss" scoped>
.overflow-scroll {
  overflow-y: auto;
}

.vertical-nav-drawer {
  width: clamp(180px, 16vw, 320px) !important;
  min-width: 180px !important;
  max-width: 320px !important;
  :deep(.q-drawer__content) {
    overflow: hidden;
  }
}

.levers-col {
  width: clamp(180px, 30vw, 600px) !important;
  min-width: 180px !important;
  max-width: 600px !important;
  scrollbar-gutter: stable;
  align-items: center;
  justify-content: center;
  justify-items: center;
}

.header-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  font-size: 20px;
  margin-right: 12px;
  opacity: 0.7;
  transition: opacity 150ms ease;
}

.header-text {
  flex: 1;
}

.right-column {
  flex: 1;
  max-height: 100%;
  overflow: hidden;
}
</style>
