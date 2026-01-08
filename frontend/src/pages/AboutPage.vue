<template>
  <q-page class="q-pa-md">
    <div class="container q-pa-md">
      <h1 class="text-h3 text-weight-bold q-mb-lg">{{ $t('aboutTitle') }}</h1>

      <div class="content-section">
        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">{{ $t('ourMission') }}</h2>
          <p class="text-body1 text-grey-8">
            {{ $t('ourMissionDesc') }}
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">{{ $t('whatWeOffer') }}</h2>
          <p class="text-body1 text-grey-8 q-mb-md">
            {{ $t('whatWeOfferDesc') }}
          </p>
          <q-list bordered separator>
            <q-item
              v-for="sector in displaySectors"
              :key="sector.value"
              clickable
              :to="getNavigationTarget(sector.value)"
            >
              <q-item-section avatar>
                <q-icon color="primary" :name="sector.icon" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-medium">
                  {{ getLabel(sector.label) }}
                </q-item-label>
                <q-item-label v-if="sector.description" caption>
                  {{ getLabel(sector.description) }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">{{ $t('howItWorks') }}</h2>
          <p class="text-body1 text-grey-8">
            {{ $t('howItWorksDesc') }}
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">{{ $t('theTeam') }}</h2>
          <p class="text-body1 text-grey-8">
            {{ $t('theTeamDesc') }}
          </p>
        </section>

        <div class="text-center q-mt-xl">
          <q-btn
            color="primary"
            :label="$t('tryCalculator')"
            :to="getNavigationTarget('overall')"
            size="lg"
            icon-right="calculate"
            unelevated
          />
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useSectorNavigation } from 'src/composables/useSectorNavigation';
import { getTranslatedText, type TranslationObject } from 'src/utils/translationHelpers';

const { locale } = useI18n();
const { availableSectors, getNavigationTarget } = useSectorNavigation();

const displaySectors = computed(() => availableSectors.value.filter((s) => !s.disabled));
const getLabel = (label: string | TranslationObject) => getTranslatedText(label, locale.value);
</script>

<style lang="scss" scoped>
.container {
  max-width: 900px;
  margin: 0 auto;
}

.content-section {
  line-height: 1.8;
}

section {
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
