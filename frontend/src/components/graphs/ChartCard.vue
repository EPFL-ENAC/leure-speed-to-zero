<template>
  <q-card class="chart-card col" flat>
    <q-card-section class="chart-section">
      <div v-if="!chartData.length" class="chart-placeholder">
        <q-icon name="mdi-chart-line-variant" size="2rem" color="grey-5" />
        <p>{{ $t('noDataAvailable') }}</p>
      </div>
      <div v-else class="chart-visualization">
        <div class="chart-title">{{ translatedTitle }}</div>
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
import { LineChart, BarChart, SankeyChart } from 'echarts/charts';
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
  MarkLineComponent,
  ToolboxComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';
import { plotLabels } from 'config/plotLabels';
import { useI18n } from 'vue-i18n';
import { getTranslatedText } from 'src/utils/translationHelpers';
import { getSeriesConfig } from 'src/utils/chartTypes';

const i18n = useI18n();
const { t } = i18n;

// Register ECharts components
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  SankeyChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  DataZoomComponent,
  MarkAreaComponent,
  ToolboxComponent,
  MarkLineComponent,
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
  value: number | [number, number];
  marker: string;
}

// Props
const props = defineProps<{
  chartConfig: ChartConfig;
  modelData: SectorData;
  chartId?: string;
  sectorName?: string;
}>();

const chartRef = ref<ECharts>();

// Track legend selection state
const legendSelected = ref<Record<string, boolean>>({});

// Computed property for translated chart title
const translatedTitle = computed<string>(() => {
  return getTranslatedText(props.chartConfig.title, i18n.locale.value);
}); // Handle legend selection changes
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
        name: getTranslatedText(plotLabels[outputId] || outputId, i18n.locale.value, outputId),
        color: outputConfig.color || null,
        years,
        data: values,
      });
    }
  });

  return series;
}

// Function to download chart data as CSV
function downloadCSV() {
  if (!chartData.value.length) return;

  // Collect all unique years from all series
  const allYears = new Set<number>();
  chartData.value.forEach((series) => {
    series.years.forEach((year) => allYears.add(year));
  });
  const sortedYears = Array.from(allYears).sort((a, b) => a - b);

  // Create CSV header
  const headers = ['Year', ...chartData.value.map((series) => series.name)];
  const csvRows = [headers.join(',')];

  // Create CSV data rows
  sortedYears.forEach((year) => {
    const row = [year.toString()];
    chartData.value.forEach((series) => {
      const yearIndex = series.years.indexOf(year);
      if (yearIndex !== -1) {
        const dataPoint = series.data[yearIndex];
        const value = Array.isArray(dataPoint) ? dataPoint[1] : dataPoint;
        row.push(value !== undefined ? value.toString() : '');
      } else {
        row.push('');
      }
    });
    csvRows.push(row.join(','));
  });

  // Create and download the CSV file
  const csvContent = csvRows.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);

  link.setAttribute('href', url);
  link.setAttribute(
    'download',
    `${translatedTitle.value.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.csv`,
  );
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Format data for ECharts
const chartOption = computed(() => {
  if (!chartData.value.length) return {};

  // Get the max year from data to determine chart end
  const maxYear = Math.max(...chartData.value.flatMap((series) => series.years));

  // Create mark area configuration for forecast period
  const forecastMarkArea = {
    silent: true,
    itemStyle: {
      color: 'transparent', // No background fill
    },
    label: {
      show: true,
      position: 'top',
      fontSize: 11,
      color: '#666',
    },

    data: [
      [
        {
          name: t('historical'),
          xAxis: new Date(1990, 0, 1).getTime(), // January 1st, 1990
        },
        {
          xAxis: new Date(2024, 0, 1).getTime(), // January 1st, 2024
        },
      ],
      [
        {
          name: t('forecast'),
          xAxis: new Date(2024, 0, 1).getTime(), // January 1st, 2024
        },
        {
          xAxis: new Date(maxYear, 11, 31).getTime(), // December 31st of max year
        },
      ],
    ],
  };

  // Create mark area configuration for the transition period (2023-2025)
  const transitionMarkArea = {
    silent: true,
    itemStyle: {
      color: 'rgba(0, 0, 0, 0.1)',
      borderColor: 'rgba(0, 0, 0, 0.06)',
      borderWidth: 2,
      borderType: 'dashed',
    },

    data: [
      [
        {
          xAxis: new Date(2023, 0, 1).getTime(),
        },
        {
          xAxis: new Date(2025, 0, 1).getTime(),
        },
      ],
    ],
  };

  // Create series array for ECharts
  const seriesConfig = getSeriesConfig(props.chartConfig.type);
  const series = chartData.value.map((series) => ({
    name: series.name,
    ...seriesConfig,
    z: 0,
    itemStyle: { color: series.color },
    data: series.data,
  }));

  // Create the invisible series with mark areas - put them first so they're rendered last (on top)
  const markAreaSeriesForecast = {
    name: '__mark_forecast__', // Hidden series name
    type: 'line',
    data: [], // No data points
    symbol: 'none',
    z: 100,
    zlevel: 10,
    markArea: {
      ...forecastMarkArea,
      z: 10,
    },
    legendHoverLink: false,
  };

  const markAreaSeriesTransition = {
    name: '__mark_transition__', // Hidden series name
    type: 'line',
    data: [], // No data points
    symbol: 'none',
    z: 100,
    zlevel: 10,
    markArea: {
      ...transitionMarkArea,
      z: 10,
    },
    legendHoverLink: false,
  };

  // Put mark area series at the end so they render on top
  const allSeries = [...series, markAreaSeriesForecast, markAreaSeriesTransition];
  const legendData = series.map((serie) => serie.name);

  return {
    toolbox: {
      show: true,
      right: 10,
      top: 5,
      feature: {
        dataZoom: {
          yAxisIndex: 'none',
        },
        restore: {},
        myCsvDownload: {
          show: true,
          title: t('downloadCSV'),
          icon: 'path://M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z',
          onclick: () => {
            downloadCSV();
          },
        },
      },
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: EChartsTooltipParam[]) => {
        const year = params[0]?.axisValueLabel;
        const unit = props.chartConfig.unit;
        return params.reduce((text, param, i) => {
          // Extract the value from the [timestamp, value] array
          const value = (Array.isArray(param.value) ? param.value[1] : param.value).toFixed(2);
          const val = `${text}${i === 0 ? `${year}<br/>` : ''}${param.marker} ${param.seriesName}: ${value} ${unit}<br/>`;
          return val;
        }, '');
      },
    },

    legend: {
      selector: true,
      type: 'scroll',
      orient: 'none',
      bottom: 0,
      height: '10%',
      data: legendData,
      selected: legendSelected.value,
    },
    grid: {
      top: '15%',
      left: '5%',
      right: '5%',
      bottom: '13%',
      containLabel: true,
    },
    xAxis: {
      type: 'time',
      z: -1,
      // boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      name: props.chartConfig.unit,
      nameLocation: 'end',
      z: -1,
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
  min-width: 500px;
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
  display: flex;
  flex-direction: column;
}

.chart-title {
  position: absolute;
  color: #6a6a6a;
  top: 0px;
  left: 2rem;
  font-size: 13px;
  font-weight: bold;
  white-space: wrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: calc(100% - 150px);
}

.chart {
  flex: 1;
  min-height: 0;
}

@media screen and (max-width: 600px) {
  .chart-card {
    min-width: 100%;
    min-height: 400px;
    height: 55vh;
  }
}
</style>
