<template>
  <q-page class="home-page">
    <div class="container q-pa-md">
      <!-- Hero Section with Calculator Preview -->
      <div class="hero-section text-center q-mb-xl q-pt-xl">
        <h1 class="text-h2 text-weight-bold q-mb-md">Welcome to Speed to Zero</h1>
        <p class="text-h5 text-grey-7 q-mb-lg">
          Interactive carbon neutrality calculator for Switzerland
        </p>
        <div class="button-group q-gutter-md justify-center">
          <q-btn
            size="lg"
            color="primary"
            label="Open Calculator"
            :to="{ name: 'buildings' }"
            unelevated
            icon-right="calculate"
            class="q-px-xl"
          />
          <q-btn
            size="lg"
            outline
            color="primary"
            label="Learn More"
            :to="{ name: 'about' }"
            class="q-px-xl"
          />
        </div>
      </div>

      <!-- Quick Access to Sectors -->
      <div class="sectors-section q-mb-xl">
        <h2 class="text-h4 text-center q-mb-lg">Explore by Sector</h2>
        <div class="row q-col-gutter-md">
          <div
            v-for="sector in availableSectors"
            :key="sector.value"
            class="col-12 col-sm-6 col-md-3"
          >
            <router-link
              v-if="!sector.disabled"
              :to="getNavigationTarget(sector.value)"
              class="sector-link"
            >
              <q-card flat bordered class="sector-card full-height">
                <q-card-section class="text-center">
                  <q-icon :name="sector.icon" size="3rem" color="primary" />
                  <div class="text-h6 q-mt-md">{{ getLabel(sector.label) }}</div>
                </q-card-section>
              </q-card>
            </router-link>
            <q-card v-else flat bordered class="sector-card full-height disabled">
              <q-card-section class="text-center">
                <q-icon :name="sector.icon" size="3rem" color="primary" />
                <div class="text-h6 q-mt-md">{{ getLabel(sector.label) }}</div>
              </q-card-section>
            </q-card>
          </div>
        </div>
      </div>

      <!-- Features Section -->
      <div class="features-section q-mb-xl">
        <h2 class="text-h4 text-center q-mb-lg">How It Works</h2>
        <div class="row q-col-gutter-md">
          <div class="col-12 col-md-4">
            <div class="feature-item text-center q-pa-md">
              <div class="feature-number text-primary text-h3 text-weight-bold">1</div>
              <div class="text-h6 q-mt-md q-mb-sm">Select a Sector</div>
              <p class="text-grey-7">
                Choose from buildings, transport, energy, agriculture, or forestry
              </p>
            </div>
          </div>
          <div class="col-12 col-md-4">
            <div class="feature-item text-center q-pa-md">
              <div class="feature-number text-primary text-h3 text-weight-bold">2</div>
              <div class="text-h6 q-mt-md q-mb-sm">Adjust Policy Levers</div>
              <p class="text-grey-7">Configure interventions and see their impact in real-time</p>
            </div>
          </div>
          <div class="col-12 col-md-4">
            <div class="feature-item text-center q-pa-md">
              <div class="feature-number text-primary text-h3 text-weight-bold">3</div>
              <div class="text-h6 q-mt-md q-mb-sm">Analyze Results</div>
              <p class="text-grey-7">
                Visualize emissions, energy consumption, and key performance indicators
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { getTranslatedText, type TranslationObject } from 'src/utils/translationHelpers';
import { useSectorNavigation } from 'src/composables/useSectorNavigation';

const { locale } = useI18n();
const { availableSectors, getNavigationTarget } = useSectorNavigation();

const getLabel = (label: string | TranslationObject) => getTranslatedText(label, locale.value);
</script>

<style lang="scss" scoped>
.home-page {
  background: linear-gradient(180deg, rgba(var(--q-primary-rgb), 0.03) 0%, white 100%);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.hero-section {
  padding: 2rem 0;
}

.button-group {
  display: flex;
  flex-wrap: wrap;
}

.sector-link {
  text-decoration: none;
  display: block;
  height: 100%;
}

.sector-card {
  transition: all 0.3s ease;
  cursor: pointer;
  height: 100%;

  &:hover {
    transform: translateY(-8px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  }

  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.feature-item {
  .feature-number {
    opacity: 0.15;
  }
}

@media (max-width: 600px) {
  .hero-section {
    padding: 1rem 0;

    h1 {
      font-size: 1.75rem;
    }

    .button-group {
      flex-direction: column;

      .q-btn {
        width: 100%;
      }
    }
  }
}
</style>
