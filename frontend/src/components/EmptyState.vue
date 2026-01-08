<template>
  <div class="empty-state">
    <q-spinner-dots v-if="loading" color="primary" size="3rem" />
    <template v-else>
      <q-icon :name="icon" size="2.5rem" color="grey-5" />
      <p class="text-grey-6">{{ message }}</p>
      <q-btn
        v-if="showRefresh"
        flat
        round
        dense
        icon="refresh"
        size="md"
        color="grey-6"
        @click="emit('refresh')"
        class="q-mt-sm"
      >
        <q-tooltip>{{ refreshLabel }}</q-tooltip>
      </q-btn>
    </template>
  </div>
</template>

<script setup lang="ts">
interface Props {
  loading?: boolean;
  icon?: string;
  message: string;
  showRefresh?: boolean;
  refreshLabel?: string;
}

const {
  loading = false,
  icon = 'insights',
  showRefresh = true,
  refreshLabel = 'Refresh',
} = defineProps<Props>();

const emit = defineEmits<{
  refresh: [];
}>();
</script>

<style lang="scss" scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 0.75rem;
  text-align: center;
  padding: 2rem;

  p {
    margin: 0;
    font-size: 0.9rem;
  }
}
</style>
