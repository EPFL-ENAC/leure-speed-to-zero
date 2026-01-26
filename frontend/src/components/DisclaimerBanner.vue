<template>
  <q-banner dense class="text-orange-7 text-center bg-yellow-1">
    <div class="text-caption text-weight-medium">
      <q-icon name="warning" size="xs" class="q-pr-sm" />
      <span class="gt-md">{{ $t('welcomePopup.disclaimer') }}</span>
      <span class="lt-lg">{{ $t('welcomePopup.disclaimerShort') }}</span>
    </div>
  </q-banner>
</template>

<script setup lang="ts">
// Simple presentation component using QBanner
</script>
