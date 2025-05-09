<template>
  <q-card class="chart-card">
    <q-card-section>
      <div class="text-h6">{{ chartConfig.title }}</div>
    </q-card-section>
    <q-card-section>
      <div class="chart-container">
        <div v-if="!chartData.length" class="chart-placeholder">
          <p>No data available for this chart</p>
        </div>
        <div v-else class="chart-visualization">
          <v-chart class="chart" :option="chartOption" autoresize />
        </div>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  DataZoomComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';

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

// Define types for output configuration
interface OutputConfig {
  id: string;
  color?: string;
}

// Define types for chart data series
interface ChartSeries {
  name: string;
  color: string | null;
  years: number[];
  data: number[];
}

// Define type for year data
interface YearData {
  year: number;
  [key: string]: unknown;
}

// Define type for ECharts tooltip params
interface EChartsTooltipParam {
  axisValueLabel: string;
  seriesName: string;
  value: number;
  marker: string;
}

// Type for chart configuration props
interface ChartConfig {
  title: string;
  type: string;
  unit: string;
  outputs: Array<string | OutputConfig>;
}

// Type for model data props
interface ModelData {
  data?: {
    buildings?: {
      countries?: {
        Switzerland?: YearData[];
      };
    };
  };
}

const props = defineProps<{
  chartConfig: ChartConfig;
  modelData: ModelData;
}>();

// Extract the chart data from the model results
const chartData = computed<ChartSeries[]>(() => {
  if (!props.modelData || !props.modelData.data) {
    return [];
  }

  // Get outputs from chart config
  const outputs = props.chartConfig.outputs;
  const countryData = props.modelData.data.buildings?.countries?.Switzerland;
  debugger;
  if (!countryData || !outputs) return [];

  return extractChartData(outputs, countryData);
});

function extractChartData(
  outputs: Array<string | OutputConfig>,
  countryData: YearData[],
): ChartSeries[] {
  const series: ChartSeries[] = [];

  // Handle both array of objects and array of strings
  const outputConfigs: OutputConfig[] = outputs.map((output) => {
    if (typeof output === 'string') {
      return { id: output };
    }
    return output;
  });

  outputConfigs.forEach((outputConfig) => {
    // Parse the output ID to match data structure
    const outputId = outputConfig.id;
    // Extract the base field name (before the [unit])
    const fieldMatch = outputId.match(/(.+?)\[(.+?)\]/);

    if (!fieldMatch || !fieldMatch[1]) return;

    const fieldName = fieldMatch[1];
    const years: number[] = [];
    const values: number[] = [];

    countryData.forEach((yearData: YearData) => {
      if (fieldName in yearData) {
        years.push(yearData.year);
        // Using type assertion here since we've verified fieldName exists in yearData
        values.push(yearData[fieldName] as number);
      }
    });

    if (years.length > 0) {
      series.push({
        name: outputId,
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
  if (!chartData.value.length) {
    return {};
  }

  // Get unique years from all series
  const allYears = chartData.value.flatMap((series) => series.years);
  const uniqueYears = [...new Set(allYears)].sort();
  console.log('Unique years:', uniqueYears);
  // Create series array for ECharts
  const series = chartData.value.map((series) => {
    return {
      name: series.name,
      type: props.chartConfig.type.toLowerCase() === 'stackedarea' ? 'line' : 'bar',
      stack: props.chartConfig.type.toLowerCase() === 'stackedarea' ? 'total' : null,
      areaStyle: props.chartConfig.type.toLowerCase() === 'stackedarea' ? {} : null,
      emphasis: {
        focus: 'series',
      },
      itemStyle: {
        color: series.color,
      },
      data: series.data,
    };
  });

  return {
    tooltip: {
      trigger: 'axis',
      formatter: function (params: EChartsTooltipParam[]) {
        let result = params[0]?.axisValueLabel + '<br/>';
        params.forEach((param) => {
          result += `${param.marker} ${param.seriesName}: ${param.value} ${props.chartConfig.unit}<br/>`;
        });
        return result;
      },
    },
    legend: {
      type: 'scroll',
      orient: 'horizontal',
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '3%',
      containLabel: true,
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        start: 0,
        end: 100,
      },
    ],
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: uniqueYears,
    },
    yAxis: {
      type: 'value',
      name: props.chartConfig.unit,
      nameLocation: 'end',
      nameTextStyle: {
        padding: [0, 0, 0, 5],
      },
    },
    series: series,
  };
});
</script>

<style lang="scss" scoped>
.chart-card {
  height: 400px;
}

.chart-container {
  height: 300px;
}

.chart-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #f0f8ff;
  border-radius: 8px;
}

.chart-visualization {
  height: 100%;
  width: 100%;
}

.chart {
  height: 100%;
  width: 100%;
}
</style>
