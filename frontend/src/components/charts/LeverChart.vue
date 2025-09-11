<template>
  <div class="lever-chart-container" :style="{ height, width }">
    <div v-if="leverStore.isLoadingLeverData" class="flex flex-center q-pa-lg">
      <q-spinner-dots size="2rem" />
      <span class="q-ml-sm">Loading chart data...</span>
    </div>

    <div v-else-if="leverStore.leverDataError" class="text-negative q-pa-md text-center">
      <q-icon name="error" size="2rem" class="q-mb-sm" />
      <div>{{ leverStore.leverDataError }}</div>
      <q-btn
        @click="fetchData"
        color="primary"
        outline
        size="sm"
        class="q-mt-md"
        :loading="leverStore.isLoadingLeverData"
      >
        Retry
      </q-btn>
    </div>

    <div v-else-if="!chartData.length" class="text-center q-pa-md text-grey-7">
      No chart data available
    </div>

    <v-chart
      v-else
      ref="chartRef"
      :option="chartOption"
      autoresize
      style="height: 100%; width: 100%"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';
import { useLeverStore } from 'stores/leversStore';
import type { LeverYearData } from 'stores/leversStore';
import { getPlotLabel } from 'utils/labelsPlot';
import { type Lever, levers as leversConfigs } from 'src/utils/leversData';

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
const props = withDefaults(
  defineProps<{
    leverCode: string;
    height?: string;
    width?: string;
  }>(),
  {
    height: '40vh',
    width: '100%',
  },
);

// State
const chartRef = ref(null);
const leverStore = useLeverStore();

const leverConfig = computed(() => {
  const conf = leversConfigs.find((l) => l.code === props.leverCode) as Lever;
  return conf;
});

const leverValue = computed(() => {
  return leverStore.getLeverValue(leverConfig.value.code);
});

const fetchData = async () => {
  try {
    await leverStore.fetchLeverData(props.leverCode);
  } catch (error) {
    console.error('Failed to fetch lever data:', error);
  }
};

// Fetch data when lever code change
watch(
  () => props.leverCode,
  async () => {
    if (props.leverCode) {
      await fetchData();
    }
  },
  { immediate: true },
);

// Extract chart data from lever results - simplified approach
const chartData = computed(() => {
  if (!leverStore.leverData?.data?.lever_positions) {
    return [];
  }

  const leverPositions = leverStore.leverData.data.lever_positions;
  const metadata = leverStore.leverData.data.metadata;

  const leverData = leverPositions[leverValue.value];
  debugger;
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

// Expose the chart ref for external access if needed
defineExpose({
  chartRef,
});
</script>

<style lang="scss" scoped>
.lever-chart-container {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
