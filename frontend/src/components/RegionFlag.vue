<template>
  <div class="region-flag" :title="`Region: ${currentRegion}`">
    <img :src="regionFlag" :alt="`${currentRegion} flag`" />
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
  width: fit-content;
  max-width: 6rem;
  max-height: 3rem;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid rgba(67, 67, 67, 0.741);
}

.region-flag img {
  width: 4rem;
  height: auto;
  max-width: 6rem;
  max-height: 3rem;
  object-fit: contain;
}
</style>
