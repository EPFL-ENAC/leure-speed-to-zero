<template>
  <div
    class="region-flag"
    :title="`Region: ${currentRegion}`"
    :class="{ 'vaud-region': currentRegion.toLowerCase() === 'vaud' }"
  >
    <img
      :src="regionFlag"
      :alt="`${currentRegion} flag`"
      :class="{ 'rotate-90': currentRegion.toLowerCase() === 'vaud' }"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { getCurrentRegion } from 'src/utils/region';
import vaudFlag from 'src/assets/flags/vaud.svg';
import switzerlandFlag from 'src/assets/flags/switzerland.svg';

const currentRegion = computed(() => getCurrentRegion());

const regionFlag = computed(() => {
  const region = currentRegion.value.toLowerCase();
  if (region === 'vaud') return vaudFlag;
  if (region === 'switzerland') return switzerlandFlag;
  return switzerlandFlag; // Default fallback
});
</script>

<style scoped>
.region-flag {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 3rem;
  min-width: 6rem;
  border-radius: 4px;
  overflow: visible;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.region-flag.vaud-region {
  height: 5rem;
}

.region-flag img {
  height: 100%;
  width: auto;
  max-width: none;
  object-fit: contain;
}

.region-flag img.rotate-90 {
  transform: rotate(90deg);
}
</style>
