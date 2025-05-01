<template>
  <q-page class="row">
    <!-- Left sidebar for levers -->
    <div class="col-3 bg-grey-2 lever-sidebar">
      <q-scroll-area style="height: 100%">
        <div class="q-pa-md">
          <div class="text-h5 q-mb-md">Climate Action Levers</div>
          <q-separator class="q-mb-md" />

          <q-select
            v-model="selectedPathway"
            :options="pathwayOptions"
            label="Select Pathway"
            outlined
            dense
            emit-value
            map-options
            class="q-mb-md"
          />

          <q-btn
            label="Reset to Defaults"
            color="grey"
            flat
            class="full-width q-mb-md"
            @click="resetToDefaults"
          />

          <LeverGroups />
        </div>
      </q-scroll-area>
    </div>

    <!-- Main content area for results -->
    <div class="col-9 main-content">
      <div class="q-pa-md">
        <div class="text-h4 q-mb-md">Climate Model Results</div>
        <p class="text-body1 q-mb-md">
          Adjust the levers in the sidebar to create your pathway to zero emissions.
        </p>

        <q-btn
          label="Run Model"
          color="primary"
          size="lg"
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

        <div v-else-if="!isLoading && !error" class="text-center q-mt-xl text-grey">
          <q-icon name="analytics" size="4rem" />
          <p class="q-mt-md">Run the model to see results</p>
        </div>

        <q-inner-loading :showing="isLoading">
          <q-spinner-dots size="50px" color="primary" />
        </q-inner-loading>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useLeverStore } from 'stores/leversStore';
import { ExamplePathways } from 'utils/examplePathways';
import LeverGroups from 'components/LeverGroups.vue';

const leverStore = useLeverStore();

// Pathway selection
const selectedPathway = computed({
  get: () => leverStore.selectedPathway,
  set: (value) => {
    if (value) {
      leverStore.applyPathway(value);
    }
  },
});

// Create pathway options for dropdown
const pathwayOptions = computed(() => {
  return ExamplePathways.map((pathway) => ({
    label: pathway.title,
    value: pathway.title,
  }));
});

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
    // Error is now handled by the store and displayed via the error computed property
  }
}

function resetToDefaults() {
  leverStore.resetToDefaults();
}

function dismissError() {
  leverStore.error = null;
}
</script>

<style lang="scss" scoped>
.lever-sidebar {
  border-right: 1px solid #e0e0e0;
  height: calc(100vh - 50px);
}

.main-content {
  height: calc(100vh - 50px);
  overflow-y: auto;
}

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
