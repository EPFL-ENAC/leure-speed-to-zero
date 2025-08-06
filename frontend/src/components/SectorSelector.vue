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

interface Sector {
  label: string;
  value: string;
  icon: string;
}

const route = useRoute();
const router = useRouter();

const miniState = ref(true);
const drawer = ref(false);

const sectors: Sector[] = [
  { label: 'Buildings', value: 'buildings', icon: 'apartment' },
  { label: 'Transport', value: 'transport', icon: 'bike_scooter' },
  { label: 'Agriculture', value: 'agriculture', icon: 'agriculture' },
  { label: 'Forestry', value: 'forestry', icon: 'forest' },
  { label: 'Waste', value: 'waste', icon: 'delete' },
  { label: 'Energy', value: 'energy', icon: 'solar_power' },
  { label: 'Industry', value: 'industry', icon: 'factory' },
  { label: 'Water', value: 'water', icon: 'water_drop' },
  { label: 'Mining', value: 'mining', icon: 'hardware' },
  { label: 'Tourism', value: 'tourism', icon: 'luggage' },
  { label: 'Healthcare', value: 'healthcare', icon: 'local_hospital' },
  { label: 'Education', value: 'education', icon: 'school' },
  { label: 'Finance', value: 'finance', icon: 'account_balance' },
  { label: 'Retail', value: 'retail', icon: 'shopping_cart' },
  { label: 'Technology', value: 'technology', icon: 'computer' },
  { label: 'Aviation', value: 'aviation', icon: 'flight' },
  { label: 'Shipping', value: 'shipping', icon: 'directions_boat' },
  { label: 'Construction', value: 'construction', icon: 'construction' },
  { label: 'Textiles', value: 'textiles', icon: 'dry_cleaning' },
  { label: 'Food Processing', value: 'food-processing', icon: 'restaurant' },
  { label: 'Pharmaceuticals', value: 'pharmaceuticals', icon: 'medication' },
  { label: 'Chemicals', value: 'chemicals', icon: 'science' },
  { label: 'Paper & Pulp', value: 'paper-pulp', icon: 'description' },
  { label: 'Steel & Metals', value: 'steel-metals', icon: 'build' },
  { label: 'Cement', value: 'cement', icon: 'concrete' },
  { label: 'Telecommunications', value: 'telecommunications', icon: 'cell_tower' },
  { label: 'Entertainment', value: 'entertainment', icon: 'theaters' },
  { label: 'Sports', value: 'sports', icon: 'sports_soccer' },
];

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
