<template>
  <q-page class="q-pa-md">
    <div class="container q-pa-md">
      <h1 class="text-h3 text-weight-bold q-mb-lg">{{ $t('legalNotice') }}</h1>

      <div class="content-section">
        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">{{ $t('termsOfUse') }}</h2>
          <p class="text-body1 text-grey-8">
            {{ $t('termsOfUseDesc') }}
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">{{ $t('privacyPolicy') }}</h2>
          <p class="text-body1 text-grey-8">
            {{ $t('privacyPolicyDesc') }}
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">{{ $t('dataUsage') }}</h2>
          <p class="text-body1 text-grey-8">
            {{ $t('dataUsageDesc') }}
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">{{ $t('disclaimer') }}</h2>
          <p class="text-body1 text-grey-8">
            {{ $t('disclaimerDesc') }}
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">{{ $t('intellectualProperty') }}</h2>
          <p class="text-body1 text-grey-8">
            {{ $t('intellectualPropertyDesc') }}
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">{{ $t('contact') }}</h2>
          <p class="text-body1 text-grey-8">
            {{ $t('contactDesc') }}
          </p>
        </section>

        <q-separator color="grey-3" class="q-my-lg" />

        <div class="text-caption text-grey-6 text-center">
          {{ $t('lastUpdated') }}: {{ formattedDate }}
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { locale } = useI18n();

const formattedDate = computed(() => {
  return new Date().toLocaleDateString(locale.value);
});
</script>

<style lang="scss" scoped>
.container {
  max-width: 900px;
  margin: 0 auto;
}

.content-section {
  line-height: 1.8;
}
</style>
