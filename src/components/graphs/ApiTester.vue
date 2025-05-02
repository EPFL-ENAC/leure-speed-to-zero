<template>
  <div>
    <div class="text-h6 q-mb-md">API Test</div>
    <p class="text-body1 q-mb-md">
      Run the model with current lever settings to see raw API response.
    </p>

    <q-btn
      label="Run Model"
      color="primary"
      :loading="isLoading"
      @click="runModel"
      class="q-mb-xl"
    />

    <!-- Error alert -->
    <q-banner v-if="error" rounded class="bg-negative text-white q-mb-md">
      <template v-slot:avatar>
        <q-icon name="error" color="white" />
      </template>
      Error: {{ error }}
      <template v-slot:action>
        <q-btn flat color="white" label="Dismiss" @click="dismissError" />
      </template>
    </q-banner>

    <div v-if="modelResults" class="model-results">
      <q-card flat bordered>
        <q-card-section>
          <div class="text-h6">Model Output</div>
          <q-separator class="q-my-md" />

          <div v-if="typeof modelResults === 'object'" class="results-content">
            <q-list v-for="(value, key) in modelResults" :key="key">
              <q-item>
                <q-item-section>
                  <q-item-label caption>{{ key }}</q-item-label>
                  <q-item-label>
                    <pre>{{ JSON.stringify(value, null, 2) }}</pre>
                  </q-item-label>
                </q-item-section>
              </q-item>
              <q-separator spaced inset />
            </q-list>
          </div>
          <pre v-else>{{ modelResults }}</pre>
        </q-card-section>
      </q-card>
    </div>

    <div v-else-if="!isLoading && !error" class="text-center q-mt-md text-grey">
      <q-icon name="analytics" size="4rem" />
      <p class="q-mt-md">Run the model to see results</p>
    </div>

    <q-inner-loading :showing="isLoading">
      <q-spinner-dots size="50px" color="primary" />
    </q-inner-loading>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useLeverStore } from 'stores/leversStore';

const leverStore = useLeverStore();

// Access model state
const modelResults = computed(() => leverStore.modelResults);
const isLoading = computed(() => leverStore.isLoading);
const error = computed(() => leverStore.error);

// Methods
async function runModel() {
  try {
    await leverStore.runModel();
  } catch (error) {
    console.error('Error running model:', error);
  }
}

function dismissError() {
  leverStore.error = null;
}
</script>

<style lang="scss" scoped>
.model-results {
  max-width: 100%;
  overflow-x: auto;
}

.results-content {
  max-height: 60vh;
  overflow-y: auto;
}

pre {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
