<template>
  <q-layout view="hHh Lpr lff">
    <q-header v-if="$q.screen.lt.md" elevated class="bg-white text-dark">
      <q-toolbar>
        <q-btn flat round dense icon="menu" @click="drawer = !drawer" />
        <q-toolbar-title class="text-h6 text-weight-bold color-primary"
          >Speed to Zero</q-toolbar-title
        >
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="drawer"
      side="left"
      bordered
      :behavior="$q.screen.lt.md ? 'mobile' : 'desktop'"
      :width="miniMode ? 60 : 240"
      class="vertical-nav-drawer"
    >
      <VerticalNavigation :mini="miniMode" @toggle="toggleMiniMode" />
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import VerticalNavigation from 'components/VerticalNavigation.vue';

const $q = useQuasar();
const miniMode = ref(false);
const drawer = ref($q.screen.gt.sm);

const toggleMiniMode = () => {
  miniMode.value = !miniMode.value;
};

watch(
  () => $q.screen.lt.md,
  (mobileMode) => {
    if (mobileMode) {
      drawer.value = false;
      miniMode.value = false;
    } else {
      drawer.value = true;
      miniMode.value = false;
    }
  },
);
</script>

<style lang="scss" scoped>
// Responsive width for navigation drawer
.vertical-nav-drawer {
  width: clamp(180px, 18vw, 320px) !important;
  min-width: 180px !important;
  max-width: 320px !important;
  :deep(.q-drawer__content) {
    overflow: hidden;
  }
}
</style>
