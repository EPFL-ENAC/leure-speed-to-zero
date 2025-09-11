<template>
  <q-dialog v-model="isOpen" persistent>
    <q-card>
      <q-bar class="row items-center">
        <div>Lever details</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-bar>

      <q-card-section>
        <div v-if="leverStore.isLoadingLeverData" class="flex flex-center q-pa-lg">
          <q-spinner-dots size="2rem" />
          <span class="q-ml-sm">Loading lever data...</span>
        </div>

        <div v-else-if="leverStore.leverDataError" class="text-negative q-pa-md text-center">
          <q-icon name="error" size="2rem" class="q-mb-sm" />
          <div>{{ leverStore.leverDataError }}</div>
          <q-btn
            @click="fetchData"
            color="primary"
            outline
            class="q-mt-md"
            :loading="leverStore.isLoadingLeverData"
          >
            Retry
          </q-btn>
        </div>

        <div v-else-if="leverStore.leverData">
          <div class="popup-content-container">
            <div class="lever-selector-section">
              <LeverSelector
                :lever="leverConfig"
                :value="leverStore.getLeverValue(leverConfig.code)"
                variant="popup"
                @change="(value) => leverStore.setLeverValue(leverConfig.code, value)"
              />
            </div>

            <div class="chart-section" style="height: 40vh; width: 100%">
              <v-chart
                ref="chartRef"
                :option="chartOption"
                autoresize
                style="height: 100%; width: 100%"
              />
            </div>

            <!-- Popup text info -->
            <div v-if="leverConfig.popupText" class="popup-info-text">
              <div class="text-body2">{{ leverConfig.popupText }}</div>
            </div>
          </div>
        </div>

        <div v-else class="text-center q-pa-md text-grey-7">No data available</div>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat label="Close" color="primary" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useLeverStore } from 'stores/leversStore';
import LeverSelector from 'components/LeverSelector.vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { type Lever, levers as leversConfigs } from 'src/utils/leversData';
import { LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';
import type { LeverYearData } from 'stores/leversStore';
import { getPlotLabel } from 'utils/labelsPlot';

// Types for ECharts
interface ChartSeries {
  name: string;
  years: number[];
  data: [string, number][];
}

interface TooltipParam {
  axisValueLabel: string;
  marker: string;
  seriesName: string;
  value: [number, number];
}

// Register ECharts components
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
]);

// Props
const props = defineProps<{
  leverName: string;
  modules?: string;
  country?: string;
}>();

// Model for dialog visibility
const isOpen = defineModel<boolean>({ default: false });

// State
const chartRef = ref(null);
const leverStore = useLeverStore();

const leverConfig = computed(() => {
  const conf = leversConfigs.find((l) => l.code === props.leverName) as Lever;
  return conf;
});

// Fetch data when dialog opens
watch(isOpen, (newValue) => {
  if (newValue) {
    void fetchData();
  }
});

const fetchData = async () => {
  try {
    await leverStore.fetchLeverData(props.leverName, props.modules, props.country);
  } catch (error) {
    console.error('Failed to fetch lever data:', error);
  }
};

// Extract chart data from lever results - simplified approach
const chartData = computed(() => {
  if (!leverStore.leverData?.data?.lever_positions) {
    return [];
  }

  const leverPositions = leverStore.leverData.data.lever_positions;
  const metadata = leverStore.leverData.data.metadata;

  const leverData = leverPositions[leverStore.getLeverValue(leverConfig.value.code)];
  if (!Array.isArray(leverData) || leverData.length === 0) {
    return [];
  }

  const series: ChartSeries[] = [];
  const years = metadata?.years || [];
  // Get all variable names from metadata
  const variableNames = metadata?.variables || [];

  // Process each variable to create a series
  variableNames.forEach((varName) => {
    const data: [string, number][] = [];
    const unit = metadata?.units?.[varName] || '';
    const fullVarName = `${varName}[${unit}]`;

    // Extract data points for this variable
    leverData.forEach((record: LeverYearData) => {
      const value = record[fullVarName];
      if (typeof value === 'number' && !isNaN(value)) {
        data.push([String(record.Years), value]);
      }
    });

    if (data.length > 0) {
      // Clean up the display name
      const displayName = getPlotLabel(varName);
      series.push({
        name: displayName,
        years,
        data,
      });
    }
  });

  return series;
});

// Get the unit for the chart
const chartUnit = computed(() => {
  const metadata = leverStore.leverData?.data?.metadata;
  const firstVar = metadata?.variables?.[0];
  return (firstVar && metadata?.units?.[firstVar]) || '';
});

// Chart configuration
const chartOption = computed(() => {
  if (!chartData.value.length) {
    return {};
  }
  const series = chartData.value.map((series) => ({
    name: series.name,
    type: 'line',
    symbol: 'none',
    data: series.data,
  }));
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params: TooltipParam[]) => {
        const year = params[0]?.axisValueLabel;
        let tooltip = `${year}<br/>`;
        params.forEach((param: TooltipParam) => {
          tooltip += `${param.marker} ${param.seriesName}: ${param.value[1]} ${chartUnit.value}<br/>`;
        });
        return tooltip;
      },
    },
    legend: {
      orient: 'horizontal',
      type: 'scroll',
      bottom: '10%',
      height: '30%',
      width: '80%',
    },
    grid: {
      top: '10%',
      bottom: '20%',
      containLabel: true,
    },
    xAxis: {
      type: 'time',
    },
    yAxis: {
      type: 'value',
      name: chartUnit.value,
      nameLocation: 'end',
      nameTextStyle: { padding: [0, 0, 0, 5] },
      axisLabel: {
        formatter: function (value: number) {
          // Use scientific notation for values larger than 10,000 or smaller than 0.001
          if (Math.abs(value) >= 10000 || (Math.abs(value) > 0 && Math.abs(value) < 0.001)) {
            return value.toExponential(2);
          }
          return value;
        },
      },
    },
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: 0,
        filterMode: 'none',
      },
      {
        type: 'slider',
        xAxisIndex: 0,
        filterMode: 'none',
        bottom: '1%',
        height: 30,
      },
    ],
    series,
  };
});
</script>

<style lang="scss" scoped>
.q-card {
  max-width: 800px;
  width: 90vw;
}

// Responsive adjustments for mobile
@media screen and (max-width: 768px) {
  .q-card {
    max-width: 95vw !important;
    width: 100% !important;
  }
}

.popup-content-container {
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1rem;
}

.lever-selector-section {
  max-width: 400px;
  margin: auto;
  width: 100%;
  border: 1px solid #c3c3c3;
  padding: 1.5rem;
  border-radius: 8px;
}

.popup-info-text {
  border-left: 4px solid #1976d2;
  border-radius: 4px;
  padding: 10px;
  margin: 2rem 0;
  .text-body2 {
    line-height: 1.5;
  }
}
</style>
