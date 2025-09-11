<template>
  <q-dialog v-model="isOpen" persistent>
    <q-card>
      <q-bar class="row items-center">
        <div>Lever details</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-bar>

      <q-card-section>
        <div class="popup-content-container">
          <div class="lever-selector-section">
            <LeverSelector
              :lever="leverConfig"
              :value="leverStore.getLeverValue(leverConfig.code)"
              variant="popup"
              @change="(value) => leverStore.setLeverValue(leverConfig.code, value)"
            />
          </div>

          <div class="chart-section" style="height: 40vh; width: 100%">
            <LeverChart :lever-code="props.leverName" height="40vh" width="100%" />
          </div>

          <!-- Popup text info -->
          <div v-if="leverConfig.popupText" class="popup-info-text">
            <div class="text-body2">{{ leverConfig.popupText }}</div>
          </div>
        </div>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat label="Close" color="primary" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useLeverStore } from 'stores/leversStore';
import LeverSelector from 'components/LeverSelector.vue';
import LeverChart from 'components/charts/LeverChart.vue';
import { type Lever, levers as leversConfigs } from 'src/utils/leversData';

// Props
const props = defineProps<{
  leverName: string;
  modules?: string;
  country?: string;
}>();

// Model for dialog visibility
const isOpen = defineModel<boolean>({ default: false });

// State
const leverStore = useLeverStore();

const leverConfig = computed(() => {
  const conf = leversConfigs.find((l) => l.code === props.leverName) as Lever;
  return conf;
});
</script>

<style lang="scss" scoped>
.q-card {
  max-width: 800px;
  width: 90vw;
}

// Responsive adjustments for mobile
@media screen and (max-width: 768px) {
  .q-card {
    max-width: 95vw !important;
    width: 100% !important;
  }
}

.popup-content-container {
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem;
}

.lever-selector-section {
  max-width: 400px;
  margin: auto;
  width: 100%;
  border: 1px solid #c3c3c3;
  padding: 1.5rem;
  border-radius: 8px;
}

.popup-info-text {
  border-left: 4px solid #1976d2;
  border-radius: 4px;
  padding: 10px;
  margin: 2rem 0;
  .text-body2 {
    line-height: 1.5;
  }
}
</style>
