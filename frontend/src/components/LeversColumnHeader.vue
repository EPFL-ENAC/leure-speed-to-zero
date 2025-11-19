<template>
  <div class="levers-header">
    <q-icon name="tune" class="header-icon" />
    <span class="header-text">{{ $t('levers') }}</span>
    <q-spinner-oval v-if="isLoading" color="primary" size="1.5em" class="loading-spinner" />
    <transition name="fade">
      <q-icon
        v-if="showSuccess"
        name="check_circle"
        color="primary"
        size="1.5em"
        class="success-icon"
      />
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useLeverStore } from 'stores/leversStore';

const leverStore = useLeverStore();

const isLoading = computed(() => leverStore.isLoading);
const showSuccess = ref(false);
let successTimer: ReturnType<typeof setTimeout> | null = null;

// Watch for loading state changes
watch(isLoading, (newValue, oldValue) => {
  // When loading stops (transitions from true to false)
  if (oldValue === true && newValue === false) {
    // Clear any existing timer
    if (successTimer) {
      clearTimeout(successTimer);
    }
    // Show success icon
    showSuccess.value = true;
    // Hide after 1 second
    successTimer = setTimeout(() => {
      showSuccess.value = false;
    }, 1000);
  }
});
</script>

<style lang="scss" scoped>
.levers-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  background: #ffffff;
}

.header-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  font-size: 20px;
  opacity: 0.7;
  transition: opacity 150ms ease;
}

.header-text {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #6e6e73;
  letter-spacing: 0.02em;
}

.loading-spinner,
.success-icon {
  flex-shrink: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
