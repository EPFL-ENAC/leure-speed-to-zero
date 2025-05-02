<template>
  <div>
    <div class="text-h6 q-mb-md">Energy Graph</div>
    <div class="graph-container">
      <!-- Graph will be rendered here once implemented -->
      <div v-if="!modelResults" class="graph-placeholder">
        <q-icon name="insights" size="4rem" />
        <p>Run the model to see energy data</p>
        <q-btn
          label="Run Model"
          color="primary"
          :loading="isLoading"
          @click="runModel"
          class="q-mt-md"
        />
      </div>
      <div v-else class="graph-content">
        <!-- Placeholder for actual chart library implementation -->
        <div class="chart-placeholder">
          <p class="text-weight-bold">Energy Data Visualization</p>
          <p>Total energy consumption: {{ totalEnergy }} TWh</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useLeverStore } from 'stores/leversStore';

const leverStore = useLeverStore();

// Access model state
const modelResults = computed(() => leverStore.modelResults);
const isLoading = computed(() => leverStore.isLoading);

// Computed property for displaying total energy (example)
const totalEnergy = computed(() => {
  if (!modelResults.value) return 0;
  // This is just a placeholder - replace with actual data extraction logic
  // based on your API response structure
  return Math.round(Math.random() * 500); // Just for demo
});

// Method to run the model
async function runModel() {
  try {
    await leverStore.runModel();
  } catch (error) {
    console.error('Error running model:', error);
  }
}
</script>

<style lang="scss" scoped>
.graph-container {
  height: 400px;
  width: 100%;
}

.graph-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #f5f5f5;
  border-radius: 8px;
  color: #9e9e9e;
}

.graph-content {
  height: 100%;
  width: 100%;
}

.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #f0fff0;
  border-radius: 8px;
  padding: 1rem;
}
</style>
