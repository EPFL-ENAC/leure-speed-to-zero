<template>
  <div>
    <div class="text-h6 q-mb-md">Emissions Graph</div>
    <div class="graph-container">
      <!-- Graph will be rendered here once implemented -->
      <div v-if="!modelResults" class="graph-placeholder">
        <q-icon name="show_chart" size="4rem" />
        <p>Run the model to see emissions data</p>
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
          <p class="text-weight-bold">Emissions Data Visualization</p>
          <p>Total emissions: {{ totalEmissions }} MtCO2e</p>
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

// Computed property for displaying total emissions (example)
const totalEmissions = computed(() => {
  if (!modelResults.value) return 0;
  // This is just a placeholder - replace with actual data extraction logic
  // based on your API response structure
  return Math.round(Math.random() * 1000); // Just for demo
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
  background-color: #f0f8ff;
  border-radius: 8px;
  padding: 1rem;
}
</style>
