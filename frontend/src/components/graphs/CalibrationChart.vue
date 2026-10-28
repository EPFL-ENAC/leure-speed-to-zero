<template>
  <q-card class="chart-card col" flat>
    <q-card-section class="chart-section">
      <div v-if="!hasData" class="chart-placeholder">
        <q-icon name="mdi-chart-line-variant" size="2rem" color="grey-5" />
        <p>{{ $t('noDataAvailable') }}</p>
      </div>
      <div v-else class="chart-visualization">
        <div class="chart-title">
          {{ title }}
          <div class="chart-subtitle">
            {{
              $t('calibrationWindow', {
                start: calibration.calibration_window[0],
                end: calibration.calibration_window[1],
              })
            }}
            · {{ calibration.scope }} · <code>{{ calibration.variable }}</code>
          </div>
        </div>
        <v-chart class="chart" autoresize :option="chartOption" />
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import {
  TooltipComponent,
  LegendComponent,
  GridComponent,
  ToolboxComponent,
  MarkLineComponent,
  MarkAreaComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';
import { useI18n } from 'vue-i18n';
import type { Calibration } from 'src/composables/useCalibrationRates';

use([
  CanvasRenderer,
  LineChart,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  ToolboxComponent,
  MarkLineComponent,
  MarkAreaComponent,
]);

const props = defineProps<{
  calibration: Calibration;
  title: string;
}>();

const { t, locale } = useI18n();

// Categories whose rate is missing in every year (no reference data) are left out
const series = computed(() =>
  props.calibration.series.filter((s) => s.values.some((v) => v !== null)),
);

const hasData = computed(() => series.value.length > 0);

const formatRate = (value: number) =>
  value.toLocaleString(locale.value, { minimumFractionDigits: 3, maximumFractionDigits: 3 });

// Years down, categories across
function downloadCSV() {
  const { years } = props.calibration;
  const rows: Array<Array<string | number>> = [['Year', ...series.value.map((s) => s.name)]];
  years.forEach((year, i) => rows.push([year, ...series.value.map((s) => s.values[i] ?? '')]));

  const csv = rows.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = `calibration_${props.calibration.module}_${props.calibration.id}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

const chartOption = computed(() => {
  const [start, end] = props.calibration.calibration_window;
  const years = props.calibration.years;

  return {
    toolbox: {
      show: true,
      right: 10,
      top: 5,
      feature: {
        myCsvDownload: {
          show: true,
          title: t('downloadCSV'),
          icon: 'path://M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z',
          onclick: () => downloadCSV(),
        },
      },
    },
    tooltip: {
      trigger: 'axis',
      formatter: (
        params: Array<{ seriesName: string; value: [number, number | null]; marker: string }>,
      ) => {
        const year = params[0]?.value[0];
        const lines = params
          .filter((p) => p.value[1] !== null)
          .map((p) => `${p.marker} ${p.seriesName}: ${formatRate(p.value[1] as number)}`);
        return `${year}<br/>${lines.join('<br/>')}`;
      },
    },
    // A single series is the variable itself, already named under the title
    legend: {
      show: series.value.length > 1,
      type: 'scroll' as const,
      bottom: 0,
      textStyle: { fontSize: 11 },
    },
    grid: { top: '22%', left: '5%', right: '5%', bottom: '14%', containLabel: true },
    xAxis: {
      type: 'value' as const,
      min: years[0],
      max: years[years.length - 1],
      axisLabel: { formatter: (v: number) => String(v) },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value' as const,
      name: t('calibrationRate'),
      nameTextStyle: { padding: [0, 0, 0, 5] },
      scale: true,
    },
    series: series.value.map((s, i) => ({
      name: s.name,
      type: 'line',
      symbol: 'none',
      connectNulls: false,
      lineStyle: { width: 2 },
      data: years.map((year, j) => [year, s.values[j]]),
      // Drawn once, on the first series: the window the rates are computed
      // on, and the line at 1 (no correction)
      ...(i === 0 && {
        markArea: {
          silent: true,
          itemStyle: { color: 'rgba(0, 0, 0, 0.04)' },
          label: { show: false },
          data: [[{ xAxis: start }, { xAxis: end }]],
        },
        markLine: {
          silent: true,
          symbol: 'none',
          label: { show: false },
          lineStyle: { color: '#999', type: 'dashed', width: 1 },
          data: [{ yAxis: 1 }],
        },
      }),
    })),
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
  max-width: calc(100% - 100px);
}

.chart-subtitle {
  font-size: 11px;
  font-weight: normal;
  color: #8a8a8a;
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
