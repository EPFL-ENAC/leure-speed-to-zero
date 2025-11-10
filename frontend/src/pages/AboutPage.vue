<template>
  <q-page class="q-pa-md">
    <div class="container q-pa-md">
      <h1 class="text-h3 text-weight-bold q-mb-lg">About Speed to Zero</h1>

      <div class="content-section">
        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">Our Mission</h2>
          <p class="text-body1 text-grey-8">
            Speed to Zero is a comprehensive carbon neutrality modeling calculator designed to help
            policymakers, researchers, and organizations explore pathways to achieve net-zero
            emissions. Our mission is to provide transparent, data-driven insights into the complex
            transitions required across multiple sectors of the economy.
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">What We Offer</h2>
          <p class="text-body1 text-grey-8 q-mb-md">
            Our platform provides detailed modeling and analysis across key sectors:
          </p>
          <q-list bordered separator>
            <q-item>
              <q-item-section avatar>
                <q-icon color="primary" name="home" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-medium">Buildings Sector</q-item-label>
                <q-item-label caption
                  >Model heating, cooling, and energy efficiency improvements in residential and
                  commercial buildings</q-item-label
                >
              </q-item-section>
            </q-item>
            <q-item>
              <q-item-section avatar>
                <q-icon color="primary" name="directions_car" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-medium">Transport Sector</q-item-label>
                <q-item-label caption
                  >Analyze transitions to electric vehicles, public transport, and sustainable
                  mobility</q-item-label
                >
              </q-item-section>
            </q-item>
            <q-item>
              <q-item-section avatar>
                <q-icon color="primary" name="agriculture" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-medium">Agriculture Sector</q-item-label>
                <q-item-label caption
                  >Explore sustainable farming practices and emission reduction
                  strategies</q-item-label
                >
              </q-item-section>
            </q-item>
            <q-item>
              <q-item-section avatar>
                <q-icon color="primary" name="park" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-weight-medium">Forestry Sector</q-item-label>
                <q-item-label caption
                  >Understand carbon sequestration potential and sustainable forest
                  management</q-item-label
                >
              </q-item-section>
            </q-item>
          </q-list>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">How It Works</h2>
          <p class="text-body1 text-grey-8">
            Speed to Zero uses a sophisticated modeling engine that allows you to adjust policy
            levers and immediately see the impact on emissions, energy consumption, and other key
            metrics. The calculator combines historical data with forward-looking scenarios to
            provide comprehensive insights into potential pathways to carbon neutrality.
          </p>
        </section>

        <section class="q-mb-xl">
          <h2 class="text-h5 q-mb-md">The Team</h2>
          <p class="text-body1 text-grey-8">
            Speed to Zero is developed and maintained by EPFL (École polytechnique fédérale de
            Lausanne), bringing together expertise in climate science, energy systems, and data
            visualization.
          </p>
        </section>

        <div class="text-center q-mt-xl">
          <q-btn
            color="primary"
            label="Try Calculator"
            :to="{ name: 'buildings' }"
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
