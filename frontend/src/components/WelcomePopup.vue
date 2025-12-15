<template>
  <q-dialog v-model="showDialog" persistent>
    <q-card class="welcome-card">
      <q-card-section class="q-pt-lg q-px-lg">
        <div class="text-h4 text-weight-medium q-mb-sm">{{ $t('welcome') }}</div>
        <p class="text-body1 text-grey-7">{{ $t('welcomePopup.subtitle') }}</p>
      </q-card-section>

      <q-card-section class="q-px-lg q-pt-none">
        <div class="text-body2 text-grey-8 q-mb-md">
          {{ $t('welcomePopup.description') }}
        </div>

        <div class="features q-mb-md">
          <div v-for="feature in features" :key="feature.icon" class="feature-item q-mb-sm">
            <q-icon :name="feature.icon" size="20px" color="primary" class="q-mr-sm" />
            <span class="text-body2">{{ $t(feature.label) }}</span>
          </div>
        </div>
      </q-card-section>

      <q-card-section class="q-px-lg q-pt-none">
        <q-checkbox
          v-model="dontShowAgain"
          :label="$t('welcomePopup.dontShowAgain')"
          dense
          class="text-grey-7"
        />
      </q-card-section>

      <q-card-actions class="q-px-lg q-pb-lg">
        <q-space />
        <q-btn
          unelevated
          color="primary"
          :label="$t('welcomePopup.getStarted')"
          @click="handleClose"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const STORAGE_KEY = 'speed-to-zero-welcome-dismissed';

const showDialog = ref(false);
const dontShowAgain = ref(false);

const features = [
  { icon: 'tune', label: 'welcomePopup.featureLevers' },
  { icon: 'insights', label: 'welcomePopup.featureVisualize' },
  { icon: 'compare_arrows', label: 'welcomePopup.featureCompare' },
];

onMounted(() => {
  const dismissed = localStorage.getItem(STORAGE_KEY);
  if (!dismissed) {
    showDialog.value = true;
  }
});

const handleClose = () => {
  if (dontShowAgain.value) {
    localStorage.setItem(STORAGE_KEY, 'true');
  }
  showDialog.value = false;
};
</script>

<style lang="scss" scoped>
.welcome-card {
  max-width: 440px;
  width: 90vw;
  border-radius: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
}
</style>
