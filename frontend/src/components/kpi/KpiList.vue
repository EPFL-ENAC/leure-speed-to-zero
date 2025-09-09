<template>
  <div v-if="kpis.length > 0" class="kpi-list q-pa-md">
    <div class="row q-col-gutter-md">
      <div v-for="kpi in kpis" :key="kpi.name" class="col-12 col-sm-6 col-md-3">
        <KpiBox v-bind="kpi" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import KpiBox from './KpiBox.vue';
import { type KPI } from 'src/utils/sectors';

const { kpis } = defineProps<{
  kpis: KPI[];
}>();
</script>

<style lang="scss" scoped>
.kpi-list {
  width: 100%;
}
</style>
