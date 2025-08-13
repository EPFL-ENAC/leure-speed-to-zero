<template>
  <q-drawer
    v-model="drawer"
    show-if-above
    mini-to-overlay
    bordered
    :mini="miniState"
    @mouseenter="miniState = false"
    @mouseleave="miniState = true"
    :breakpoint="500"
    :width="200"
  >
    <div class="column full-height">
      <q-tabs
        v-model="currentSector"
        :inline-label="true"
        active-class="active"
        vertical
        class="tabs"
      >
        <q-tab
          v-for="{ label, value, icon } in sectors"
          :key="value"
          :name="value"
          :icon="icon"
          :label="label"
          :class="'tab' + miniState ? ' mini' : ''"
        />
      </q-tabs>
    </div>
  </q-drawer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { sectors } from 'utils/sectors';
const route = useRoute();
const router = useRouter();

const miniState = ref(true);
const drawer = ref(false);

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
}

:deep(.q-drawer--mini .q-tab__label) {
  color: transparent;
}
</style>
