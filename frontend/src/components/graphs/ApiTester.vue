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

          <!-- Display format toggle -->
          <div class="q-mb-md">
            <q-btn-toggle
              v-model="displayFormat"
              toggle-color="primary"
              :options="[
                { label: 'Pretty JSON', value: 'pretty' },
                { label: 'Raw JSON', value: 'raw' },
              ]"
              dense
              outline
              class="q-mb-md"
            />
          </div>

          <!-- Vue JSON Pretty view -->
          <div
            v-if="displayFormat === 'pretty' && typeof modelResults === 'object'"
            class="results-content"
          >
            <vue-json-pretty
              :data="modelResults"
              :deep="2"
              :showLength="true"
              :showDoubleQuotes="false"
              :showLineNumber="false"
              path="root"
            />
          </div>

          <!-- Original view -->
          <div v-else-if="displayFormat === 'raw'" class="results-content">
            <div v-if="typeof modelResults === 'object'">
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
          </div>

          <!-- Copy button -->
          <div class="text-right q-mt-md">
            <q-btn
              flat
              color="primary"
              icon="content_copy"
              label="Copy to Clipboard"
              @click="copyToClipboard"
            />
          </div>
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
import { computed, ref } from 'vue';
import { useLeverStore } from 'stores/leversStore';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
import { Notify } from 'quasar';

const leverStore = useLeverStore();

// Access model state
const modelResults = computed(() => leverStore.modelResults);
const isLoading = computed(() => leverStore.isLoading);
const error = computed(() => leverStore.error);
const displayFormat = ref('pretty');

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

function copyToClipboard() {
  const textToCopy =
    typeof modelResults.value === 'object'
      ? JSON.stringify(modelResults.value, null, 2)
      : String(modelResults.value);

  navigator.clipboard
    .writeText(textToCopy)
    .then(() => {
      Notify.create({
        message: 'Copied to clipboard',
        color: 'positive',
        position: 'top',
        timeout: 2000,
      });
    })
    .catch((err) => {
      console.error('Failed to copy: ', err);
      Notify.create({
        message: 'Failed to copy',
        color: 'negative',
      });
    });
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
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

pre {
  white-space: pre-wrap;
  word-break: break-word;
}

:deep(.vjs-tree) {
  font-family: monospace !important;
  font-size: 14px !important;

  .vjs-key {
    color: #0b5394 !important;
  }

  .vjs-value {
    &.vjs-value-number {
      color: #0000ff !important;
    }
    &.vjs-value-string {
      color: #008000 !important;
    }
    &.vjs-value-null {
      color: #a52a2a !important;
    }
    &.vjs-value-boolean {
      color: #9c27b0 !important;
    }
  }
}
</style>
