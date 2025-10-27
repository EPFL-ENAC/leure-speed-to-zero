<template>
  <div class="column full-height">
    <q-tabs
      v-model="currentSector"
      :inline-label="true"
      active-class="active"
      vertical
      class="tabs"
    >
      <q-tab
        v-for="{ labelKey, value, icon, disabled } in sectors"
        :key="value"
        :name="value"
        :icon="icon"
        :label="$t(labelKey)"
        :class="'tab' + (mini ? ' mini' : '') + (disabled ? ' disabled' : '')"
        :disable="disabled"
      >
        <q-tooltip v-if="disabled" class="bg-grey-8"> {{ $t('featureNotReady') }} </q-tooltip>
      </q-tab>
    </q-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { sectors } from 'utils/sectors';

const route = useRoute();
const router = useRouter();

const { mini } = defineProps<{
  mini: boolean;
}>();

// Reactive sector selection
const currentSector = ref(route.path.split('/')[1] || 'buildings');

// Watch for sector changes and update route
watch(currentSector, (newSector) => {
  if (newSector !== route.path.split('/')[1]) {
    void router.push(`/${newSector}`);
  }
});

// Watch for route changes and update current sector
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

// Expose current sector to parent
defineExpose({
  currentSector,
});
</script>

<style lang="scss" scoped>
.q-tab {
  color: #363636;
}
.active {
  background-color: $primary-background;
  color: var(--q-primary);
}

.column {
  overflow: hidden;
}

:deep(.q-tab) {
  justify-content: flex-start;
  align-items: left;
  padding: 1em;

  // Mobile adjustments
  @media (max-width: 600px) {
    padding: 0.8em;
    font-size: 0.9rem;
    min-height: 48px; // Ensure good touch targets
  }
}

:deep(.q-drawer--mini .q-tab__label) {
  color: transparent;
}

.tab.mini :deep(.q-tab__label) {
  color: transparent;
}

// Disabled tab styling
.tab.disabled :deep(.q-tab) {
  color: #a0a0a0 !important;
  pointer-events: none;
  opacity: 0.5;
}

.tab.disabled :deep(.q-tab__icon) {
  color: #a0a0a0 !important;
}

.tab.disabled :deep(.q-tab__label) {
  color: #a0a0a0 !important;
}

// Disabled tab in mini mode should also hide label
.tab.disabled.mini :deep(.q-tab__label) {
  color: transparent !important;
}
</style>
