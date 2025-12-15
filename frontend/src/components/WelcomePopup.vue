<template>
  <q-dialog v-model="showDialog" no-route-dismiss>
    <q-card class="welcome-card">
      <q-card-section class="q-pt-lg q-px-lg">
        <div class="row items-center justify-between q-mb-sm">
          <div class="text-h5 text-weight-medium">{{ $t('welcome') }}</div>
        </div>
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

      <q-card-actions class="q-px-lg q-pb-lg">
        <language-switcher />
        <q-space />
        <q-checkbox
          v-model="dontShowAgain"
          :label="$t('welcomePopup.dontShowAgain')"
          dense
          class="text-grey-7"
        />
        <q-space />
        <q-btn flat color="grey" :label="$t('welcomePopup.skipTutorial')" @click="handleSkip" />
        <q-space />
        <q-btn
          unelevated
          color="primary"
          :label="$t('welcomePopup.startTutorial')"
          @click="handleStartTutorial"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useTour } from 'src/composables/useTour';
import LanguageSwitcher from './LanguageSwitcher.vue';

const STORAGE_KEY = 'speed-to-zero-welcome-dismissed';

const showDialog = ref(true);
const dontShowAgain = ref(false);
const { startTour } = useTour();

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

const savePreference = () => {
  if (dontShowAgain.value) {
    localStorage.setItem(STORAGE_KEY, 'true');
  }
};

const handleSkip = () => {
  savePreference();
  showDialog.value = false;
};

const handleStartTutorial = () => {
  savePreference();
  showDialog.value = false;
  setTimeout(() => startTour(true), 300);
};
</script>

<style lang="scss" scoped>
.welcome-card {
  max-width: 600px;
  width: 90vw;
  border-radius: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
}
</style>
