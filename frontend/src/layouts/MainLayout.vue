<template>
  <q-layout view="hHh Lpr lff">
    <!-- Mobile Header with Menu Button -->
    <q-header v-if="$q.screen.lt.md" elevated class="bg-white text-dark">
      <q-toolbar>
        <q-btn flat round dense icon="menu" @click="drawer = !drawer" />
        <q-toolbar-title class="text-h6 text-weight-bold color-primary">
          Speed to Zero
        </q-toolbar-title>
      </q-toolbar>
    </q-header>

    <!-- Vertical Navigation Sidebar -->
    <q-drawer
      v-model="drawer"
      side="left"
      bordered
      :breakpoint="$q.screen.sizes.md"
      :width="280"
      :overlay="$q.screen.lt.md"
      class="vertical-nav-drawer"
    >
      <VerticalNavigation />
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import VerticalNavigation from 'components/VerticalNavigation.vue';

const $q = useQuasar();
const drawer = ref($q.screen.gt.md); // Start open on desktop, closed on mobile
</script>

<style lang="scss" scoped>
.vertical-nav-drawer {
  :deep(.q-drawer__content) {
    overflow: hidden;
  }
}

.q-toolbar {
  min-height: 64px;
}
</style>
