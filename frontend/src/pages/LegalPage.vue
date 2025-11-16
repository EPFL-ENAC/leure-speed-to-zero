<template>
  <q-page class="q-pa-md">
    <div class="container q-pa-md">
      <h1 class="text-h3 text-weight-bold q-mb-lg">Legal Notice</h1>

      <div class="content-section">
        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">Terms of Use</h2>
          <p class="text-body1 text-grey-8">
            By accessing and using Speed to Zero, you agree to these terms of use. This calculator
            is provided for informational and research purposes. While we strive for accuracy, the
            projections and models should not be used as the sole basis for policy or investment
            decisions.
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">Privacy Policy</h2>
          <p class="text-body1 text-grey-8">
            We respect your privacy. Speed to Zero does not collect personal information unless you
            explicitly provide it. Any data you input into the calculator remains on your device and
            is not transmitted to our servers without your consent.
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">Data Usage</h2>
          <p class="text-body1 text-grey-8">
            The underlying data used in our models comes from publicly available sources including
            Eurostat, national statistics agencies, and research institutions. All data sources are
            documented and referenced within the application.
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">Disclaimer</h2>
          <p class="text-body1 text-grey-8">
            The models and projections provided by Speed to Zero are based on assumptions and
            historical data. Actual outcomes may vary significantly. EPFL and the project
            contributors are not liable for decisions made based on the information provided by this
            calculator.
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">Intellectual Property</h2>
          <p class="text-body1 text-grey-8">
            Speed to Zero is open source software. The code and methodology are available for review
            and contribution. Please see our GitHub repository for licensing details.
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">Contact</h2>
          <p class="text-body1 text-grey-8">
            For questions, feedback, or collaboration opportunities, please contact us through the
            EPFL ENAC faculty website.
          </p>
        </section>

        <q-separator class="q-my-lg" />

        <div class="text-caption text-grey-6 text-center">
          Last updated: {{ new Date().toLocaleDateString() }}
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
// Component logic if needed
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
