<template>
  <q-card class="chart-card col" flat>
    <q-card-section class="chart-section">
      <div v-if="!chartData.length" class="chart-placeholder">
        <q-icon name="mdi-chart-line-variant" size="2rem" color="grey-5" />
        <p>No data available</p>
      </div>
      <div v-else class="chart-visualization">
        <v-chart ref="chartRef" class="chart" :option="chartOption" autoresize />
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { getCurrentRegion } from 'src/utils/region';
import { computed, ref } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart } from 'echarts/charts';
import type { SectorData, ChartConfig } from 'stores/leversStore';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  DataZoomComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';
import { getPlotLabel } from 'utils/labelsPlot';

// Register ECharts components
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  DataZoomComponent,
]);

// Types
interface ChartSeries {
  name: string;
  color: string | null;
  years: number[];
  data: number[] | [number, number][];
}

interface YearData {
  year: number;
  [key: string]: unknown;
}

interface EChartsTooltipParam {
  axisValueLabel: string;
  seriesName: string;
  value: number;
  marker: string;
}

// Props
const props = defineProps<{
  chartConfig: ChartConfig;
  modelData: SectorData;
}>();

const chartRef = ref(null);

// Extract chart data from model results
const chartData = computed<ChartSeries[]>(() => {
  if (!props.modelData) return [];

  const outputs = props.chartConfig.outputs;
  const region = getCurrentRegion();
  const countryData = props.modelData.countries?.[region];
  if (!countryData || !outputs) return [];
  return extractChartData(outputs, countryData);
});

function extractChartData(
  outputs: Array<string | { id: string; color?: string }>,
  countryData: YearData[],
): ChartSeries[] {
  const series: ChartSeries[] = [];

  // Normalize outputs to OutputConfig objects
  const outputConfigs: Array<{ id: string; color?: string }> = outputs.map((output) => {
    return typeof output === 'string' ? { id: output } : output;
  });

  outputConfigs.forEach((outputConfig) => {
    const outputId = outputConfig.id;
    const fieldMatch = outputId.match(/(.+?)\[(.+?)\]/);

    if (!fieldMatch || !fieldMatch[1]) return;

    const fieldName = fieldMatch[1];
    const years: number[] = [];
    const values: [number, number][] = [];

    countryData.forEach((yearData: YearData) => {
      if (fieldName in yearData) {
        years.push(yearData.year);
        values.push([yearData.year, yearData[fieldName] as number]);
      }
    });

    if (years.length > 0) {
      series.push({
        name: getPlotLabel(outputId),
        color: outputConfig.color || null,
        years,
        data: values,
      });
    }
  });

  return series;
}

// Format data for ECharts
const chartOption = computed(() => {
  if (!chartData.value.length) return {};

  // Create series array for ECharts
  const isStacked = props.chartConfig.type.toLowerCase() === 'stackedarea';
  const series = chartData.value.map((series) => ({
    name: series.name,
    type: isStacked ? 'line' : 'bar',
    stack: isStacked ? 'total' : undefined,
    symbol: 'none',
    areaStyle: isStacked ? {} : undefined,
    emphasis: { focus: 'series' },
    itemStyle: { color: series.color },
    data: series.data,
  }));

  return {
    title: {
      text: props.chartConfig.title,
      textStyle: {
        fontSize: 13,
        fontWeight: 'bold',
      },
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: EChartsTooltipParam[]) => {
        const year = params[0]?.axisValueLabel;
        const unit = props.chartConfig.unit;

        return params.reduce(
          (text, param, i) =>
            `${text}${i === 0 ? `${year}<br/>` : ''}${param.marker} ${param.seriesName}: ${param.value} ${unit}<br/>`,
          '',
        );
      },
    },
    legend: {
      orient: 'horizontal',
      type: 'scroll',
      bottom: '0%',
    },
    grid: {
      top: '20%',
      left: '5%',
      right: '5%',
      bottom: '10%',
      containLabel: true,
    },

    xAxis: {
      type: 'time',
      // boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      name: props.chartConfig.unit,
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
    series,
  };
});
</script>

<style lang="scss" scoped>
.chart-card {
  min-width: 400px;
  height: 450px;
  display: flex;
  flex-direction: column;
}

.chart-section {
  flex-grow: 1;
  padding-top: 8px;
}

.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #f9f9f9;
  border-radius: 8px;
  color: #999;

  p {
    margin-top: 8px;
    font-size: 0.9rem;
  }
}

.chart-visualization {
  height: 100%;
}

.chart {
  height: 100%;
}
</style>
