<template>
  <div class="lever-chart-container" :style="{ height, width }">
    <div v-if="isLoading" class="flex flex-center q-pa-lg">
      <q-spinner-dots size="2rem" />
      <span class="q-ml-sm">{{ $t('loadingChartData') }}</span>
    </div>

    <div v-else-if="error" class="text-negative q-pa-md text-center">
      <q-icon name="error" size="2rem" class="q-mb-sm" />
      <div>{{ error }}</div>
      <q-btn
        @click="fetchData"
        color="primary"
        outline
        size="sm"
        class="q-mt-md"
        :loading="isLoading"
      >
        {{ $t('retry') }}
      </q-btn>
    </div>

    <div v-else-if="!chartData.length" class="text-center q-pa-md text-grey-7">
      {{ $t('noChartDataAvailable') }}
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
import type { LeverResults, LeverYearData } from 'stores/leversStore';
import { plotLabels } from 'config/plotLabels';
import { type Lever, levers as leversConfigs } from 'src/utils/leversData';
import { useI18n } from 'vue-i18n';
import { getTranslatedText } from 'src/utils/translationHelpers';

const i18n = useI18n();

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
    minimal?: boolean;
  }>(),
  {
    minimal: false,
    height: '40vh',
    width: '100%',
  },
);

// State
const chartRef = ref(null);
const leverStore = useLeverStore();
const isLoading = ref(false);
const error = ref<string | null>(null);

const leverConfig = computed(() => {
  const conf = leversConfigs.find((l) => l.code === props.leverCode) as Lever;
  return conf;
});

const leverDataAll = ref<LeverResults | null>(null);

const leverValue = computed(() => {
  return leverStore.getLeverValue(leverConfig.value.code);
});

const fetchData = async () => {
  try {
    isLoading.value = true;
    error.value = null;
    leverDataAll.value = await leverStore.fetchLeverData(props.leverCode);
  } catch (err) {
    console.error('Failed to fetch lever data:', err);
    // Handle different types of errors
    if (err instanceof Error) {
      error.value = err.message || 'Failed to load chart data';
    } else {
      error.value = 'An unknown error occurred while loading chart data';
    }
  } finally {
    isLoading.value = false;
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
  if (!leverDataAll.value?.data?.lever_positions) {
    return [];
  }

  const leverPositions = leverDataAll.value.data.lever_positions;
  const metadata = leverDataAll.value.data.metadata;

  const leverData = leverPositions[leverValue.value];
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
      const displayName = getTranslatedText(plotLabels[varName] || varName, i18n.locale.value);
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
  const metadata = leverDataAll.value?.data?.metadata;
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
  const legendData = series.map((serie) => serie.name);

  return {
    tooltip: {
      trigger: 'axis',
      appendToBody: true,
      formatter: (params: TooltipParam[]) => {
        const year = params[0]?.axisValueLabel;
        let tooltip = `${year}<br/>`;
        params.forEach((param: TooltipParam) => {
          tooltip += `${param.marker} ${param.seriesName}: ${param.value[1].toFixed(3)} ${chartUnit.value}<br/>`;
        });
        return tooltip;
      },
    },
    legend: props.minimal
      ? undefined
      : {
          type: 'scroll',
          orient: 'none',
          bottom: 0,
          height: '15%',
          data: legendData,
          width: '90%',
        },
    grid: {
      top: props.minimal ? '15%' : '8%',
      bottom: props.minimal ? '5%' : '18%',
      containLabel: true,
      left: '0%',
      right: '0%',
      width: '100%',
    },
    xAxis: {
      type: 'time',
    },
    yAxis: {
      type: 'value',
      name: chartUnit.value,
      nameLocation: 'end',
      nameTextStyle: { padding: [0, 25, 0, 0] },
      axisLabel: {
        formatter: function (value: number) {
          // Use scientific notation for values larger than 10,000 or smaller than 0.001
          if (Math.abs(value) >= 10000 || (Math.abs(value) > 0 && Math.abs(value) < 0.001)) {
            return value.toFixed(2);
          }
          return value;
        },
      },
    },
    dataZoom: props.minimal
      ? undefined
      : [
          {
            type: 'inside',
            xAxisIndex: 0,
            filterMode: 'none',
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
