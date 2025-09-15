<template>
  <q-card class="chart-card col" flat>
    <q-card-section class="chart-section">
      <div v-if="!chartData.length" class="chart-placeholder">
        <q-icon name="mdi-chart-line-variant" size="2rem" color="grey-5" />
        <p>No data available</p>
      </div>
      <div v-else class="chart-visualization">
        <v-chart
          ref="chartRef"
          class="chart"
          autoresize
          :option="chartOption"
          @legendselectchanged="handleLegendSelectChanged"
        />
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
import type { ECharts } from 'echarts/core';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  DataZoomComponent,
  MarkAreaComponent,
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
  MarkAreaComponent,
]);

// Types
interface ChartSeries {
  name: string;
  color: string | null;
  years: number[];
  data: number[] | [number | Date, number][];
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

const chartRef = ref<ECharts>();

// Track legend selection state
const legendSelected = ref<Record<string, boolean>>({});

// Handle legend selection changes
const handleLegendSelectChanged = (params: { selected: Record<string, boolean> }) => {
  legendSelected.value = { ...params.selected };
};

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
        values.push([new Date(yearData.year, 0, 1).getTime(), yearData[fieldName] as number]);
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

  // Get the max year from data to determine chart end
  const maxYear = Math.max(...chartData.value.flatMap((series) => series.years));
  const minYear = Math.min(...chartData.value.flatMap((series) => series.years));

  // Create mark area configuration for historical period
  const historicalMarkArea = {
    silent: true,
    itemStyle: {
      color: 'rgba(76, 175, 80, 0.05)',
      borderColor: 'rgba(76, 175, 80, 0.2)',
      borderWidth: 1,
    },
    label: {
      show: true,
      position: 'insideTopLeft',
      formatter: 'Historical Data',
      fontSize: 12,
      color: '#388e3c',
      fontWeight: 'bold',
      backgroundColor: 'rgba(255, 255, 255, 0.8)',
      padding: [4, 8],
      borderRadius: 4,
    },
    data: [
      [
        {
          name: 'Historical Period',
          xAxis: new Date(minYear, 0, 1).getTime(),
        },
        {
          xAxis: new Date(2023, 11, 31).getTime(), // December 31st, 2023
        },
      ],
    ],
  };

  // Create mark area configuration for forecast period
  const forecastMarkArea = {
    silent: true,
    itemStyle: {
      color: 'rgba(74, 144, 226, 0.08)',
      borderColor: 'rgba(74, 144, 226, 0.3)',
      borderWidth: 1,
      borderType: 'dashed',
    },
    label: {
      show: true,
      position: 'insideTopRight',
      formatter: 'Model Forecast',
      fontSize: 12,
      color: '#1976d2',
      fontWeight: 'bold',
      backgroundColor: 'rgba(255, 255, 255, 0.8)',
      padding: [4, 8],
      borderRadius: 4,
    },
    data: [
      [
        {
          name: 'Forecast Period',
          xAxis: new Date(2024, 0, 1).getTime(), // January 1st, 2024
        },
        {
          xAxis: new Date(maxYear, 11, 31).getTime(), // December 31st of max year
        },
      ],
    ],
  };

  // Create series array for ECharts
  const isStacked = props.chartConfig.type.toLowerCase() === 'stackedarea';
  const series = chartData.value.map((series) => ({
    name: series.name,
    type: 'line',
    stack: isStacked ? 'total' : undefined,
    symbol: 'none',
    areaStyle: isStacked ? {} : undefined,
    itemStyle: { color: series.color },
    data: series.data,
  }));

  // Create the invisible markArea series
  const historicalMarkAreaSeries = {
    name: '__historicalMarkArea__', // Hidden series name
    type: 'line',
    data: [], // No data points
    symbol: 'none',
    lineStyle: { opacity: 0 }, // Invisible line
    markArea: historicalMarkArea,
    showSymbol: false,
    legendHoverLink: false,
  };

  // Create the forecast markArea series
  const forecastMarkAreaSeries = {
    name: '__forecastMarkArea__', // Hidden series name
    type: 'line',
    data: [], // No data points
    symbol: 'none',
    lineStyle: { opacity: 0 }, // Invisible line
    markArea: forecastMarkArea,
    showSymbol: false,
    legendHoverLink: false,
  };

  // Combine all series
  const allSeries = [...series, historicalMarkAreaSeries, forecastMarkAreaSeries];
  const legendData = series.map((serie) => serie.name);

  return {
    title: {
      text: props.chartConfig.title,
      textStyle: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#333',
      },
      left: 'center',
      top: 10,
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
      type: 'plain',
      orient: 'horizontal',
      bottom: 0,
      left: 'center',
      itemGap: 15,
      itemWidth: 14,
      itemHeight: 14,
      textStyle: {
        fontSize: 11,
      },
      data: legendData,
      selected: legendSelected.value,
    },
    grid: {
      top: '15%',
      left: '5%',
      right: '5%',
      bottom: '15%',
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
    series: allSeries,
  };
});
</script>

<style lang="scss" scoped>
.chart-card {
  min-width: 600px;
  height: 500px;
  display: flex;
  flex-direction: column;
  margin: 8px;
  
  // Responsive sizing for optimal layout
  @media screen and (min-width: 1800px) {
    min-width: 650px;
    height: 550px;
  }
  
  @media screen and (max-width: 1400px) {
    min-width: 550px;
    height: 480px;
  }
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

@media screen and (max-width: 600px) {
  .chart-card {
    min-width: 100%;
    min-height: 400px;
    height: 55vh;
  }
}
</style>
