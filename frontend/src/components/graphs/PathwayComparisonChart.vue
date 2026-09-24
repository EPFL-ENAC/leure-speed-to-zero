<template>
  <q-card class="chart-card col" flat>
    <q-card-section class="chart-section">
      <div v-if="!hasData" class="chart-placeholder">
        <q-icon name="mdi-chart-line-variant" size="2rem" color="grey-5" />
        <p>{{ $t('noDataAvailable') }}</p>
      </div>
      <div v-else class="chart-visualization">
        <div class="chart-title">{{ translatedTitle }}</div>
        <v-chart class="chart" autoresize :option="chartOption" />
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
  TooltipComponent,
  LegendComponent,
  GridComponent,
  ToolboxComponent,
} from 'echarts/components';
import VChart from 'vue-echarts';
import { useI18n } from 'vue-i18n';
import { plotLabels } from 'config/plotLabels';
import { getTranslatedText } from 'src/utils/translationHelpers';
import type { PathwayChartConfig, PathwayRun } from 'src/utils/pathwayComparison';
import type { YearData } from 'stores/leversStore';

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  ToolboxComponent,
]);

const props = defineProps<{
  chartConfig: PathwayChartConfig;
  runs: PathwayRun[];
}>();

const { t, locale } = useI18n();

const SURFACE = '#ffffff';
const DEFAULT_YEAR = 2050;

const translatedTitle = computed(() => getTranslatedText(props.chartConfig.title, locale.value));

// "field[unit]" -> "field"
const fieldOf = (outputId: string) => outputId.match(/(.+?)\[.+?\]/)?.[1] ?? outputId;

const outputs = computed(() =>
  props.chartConfig.outputs.map((o) => (typeof o === 'string' ? { id: o } : o)),
);

const scale = computed(() => props.chartConfig.scale ?? 1);

function valueOf(row: YearData | undefined, outputId: string): number | null {
  const value = row?.[fieldOf(outputId)];
  return typeof value === 'number' && Number.isFinite(value) ? value / scale.value : null;
}

// One point per year a pathway has a value for
interface LineSeries {
  name: string;
  color: string;
  dashed: boolean;
  points: Array<[year: number, value: number]>;
}

const lineSeries = computed<LineSeries[]>(() => {
  const output = outputs.value[0];
  const fromYear = props.chartConfig.fromYear ?? 0;
  if (!output) return [];

  return props.runs.map(({ pathway, rows }) => ({
    name: pathway.label,
    color: pathway.color,
    dashed: pathway.lowWaste,
    points: rows.flatMap((row): Array<[number, number]> => {
      const value = valueOf(row, output.id);
      return value === null || Number(row.year) < fromYear ? [] : [[Number(row.year), value]];
    }),
  }));
});

// One value per pathway, at the chart's year
interface BarSeries {
  name: string;
  color?: string | undefined;
  values: Array<number | null>;
}

const barYear = computed(() => props.chartConfig.year ?? DEFAULT_YEAR);

const barSeries = computed<BarSeries[]>(() => {
  const rowsAtYear = props.runs.map(({ rows }) =>
    rows.find((r) => Number(r.year) === barYear.value),
  );
  const { groups } = props.chartConfig;

  if (groups) {
    return Object.values(groups).map((group) => ({
      name: getTranslatedText(group.label, locale.value),
      color: group.color,
      values: rowsAtYear.map((row) => {
        const parts = group.outputs.map((id) => valueOf(row, id));
        return parts.some((v) => v !== null)
          ? parts.reduce<number>((sum, v) => sum + (v ?? 0), 0)
          : null;
      }),
    }));
  }

  return outputs.value.map((output) => ({
    name: getTranslatedText(plotLabels[output.id] || output.id, locale.value, output.id),
    color: output.color,
    values: rowsAtYear.map((row) => valueOf(row, output.id)),
  }));
});

const isBar = computed(() => props.chartConfig.type === 'PathwayBar');

const hasData = computed(() =>
  isBar.value
    ? barSeries.value.some((s) => s.values.some((v) => v !== null))
    : lineSeries.value.some((s) => s.points.length > 0),
);

function formatValue(value: number): string {
  return value.toLocaleString(locale.value, { maximumFractionDigits: 2 });
}

// The table behind the chart: years down, pathways across (line) or pathways
// down, components across (bar)
function downloadCSV() {
  const rows: Array<Array<string | number>> = [];
  if (isBar.value) {
    rows.push(['Pathway', ...barSeries.value.map((s) => s.name)]);
    props.runs.forEach(({ pathway }, i) =>
      rows.push([pathway.label, ...barSeries.value.map((s) => s.values[i] ?? '')]),
    );
  } else {
    const years = [...new Set(lineSeries.value.flatMap((s) => s.points.map(([y]) => y)))].sort(
      (a, b) => a - b,
    );
    rows.push(['Year', ...lineSeries.value.map((s) => s.name)]);
    years.forEach((year) =>
      rows.push([
        year,
        ...lineSeries.value.map((s) => s.points.find(([y]) => y === year)?.[1] ?? ''),
      ]),
    );
  }

  const csv = rows.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n');
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = `${translatedTitle.value.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

const toolbox = computed(() => ({
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
}));

// 12000 -> "12K", 2500000 -> "2.5M": costs and tonnes run into the millions, and
// scientific notation is hard to read them by
const valueAxisLabel = (value: number) =>
  new Intl.NumberFormat(locale.value, { notation: 'compact', maximumFractionDigits: 2 }).format(
    value,
  );

// The unit sits at the top of a vertical axis, and centered under a horizontal one
// (at its end it would run off the right edge of the card)
const unitAxis = (horizontal: boolean) => ({
  type: 'value' as const,
  name: props.chartConfig.unit,
  ...(horizontal
    ? { nameLocation: 'middle' as const, nameGap: 28 }
    : { nameLocation: 'end' as const, nameTextStyle: { padding: [0, 0, 0, 5] } }),
  axisLabel: { formatter: valueAxisLabel },
});

// Six long names wrap onto rows, so the legend must be plain (not scrolling)
// and the plot leave it room
const legend = (names: string[]) => ({
  type: 'plain' as const,
  bottom: 0,
  data: names,
  itemWidth: 18,
  itemHeight: 8,
  textStyle: { fontSize: 11 },
});

const lineOption = computed(() => ({
  toolbox: toolbox.value,
  tooltip: {
    trigger: 'axis',
    formatter: (
      params: Array<{
        axisValueLabel: string;
        seriesName: string;
        value: [number, number];
        marker: string;
      }>,
    ) =>
      params.reduce(
        (text, p, i) =>
          `${text}${i === 0 ? `${p.axisValueLabel}<br/>` : ''}${p.marker} ${p.seriesName}: ${formatValue(p.value[1])} ${props.chartConfig.unit}<br/>`,
        '',
      ),
  },
  legend: legend(lineSeries.value.map((s) => s.name)),
  grid: { top: '15%', left: '5%', right: '5%', bottom: '24%', containLabel: true },
  xAxis: { type: 'time' as const },
  yAxis: unitAxis(false),
  series: lineSeries.value.map((s) => ({
    name: s.name,
    type: 'line',
    symbol: 'none',
    lineStyle: { width: 2, type: s.dashed ? 'dashed' : 'solid', color: s.color },
    itemStyle: { color: s.color },
    data: s.points.map(([year, value]) => [new Date(year, 0, 1).getTime(), value]),
  })),
}));

// Horizontal bars, one per pathway: the long pathway names read along the
// y-axis instead of being squeezed under narrow columns.
const barOption = computed(() => {
  const categories = props.runs.map(({ pathway }) => pathway.label);
  const stacked = barSeries.value.length > 1;

  return {
    toolbox: toolbox.value,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (
        params: Array<{
          axisValueLabel: string;
          seriesName: string;
          value: number | null;
          marker: string;
        }>,
      ) => {
        const unit = props.chartConfig.unit;
        const lines = params.map(
          (p) =>
            `${p.marker} ${p.seriesName}: ${p.value === null ? '-' : formatValue(p.value)} ${unit}`,
        );
        if (stacked) {
          const total = params.reduce((sum, p) => sum + (p.value ?? 0), 0);
          lines.push(`<b>Total: ${formatValue(total)} ${unit}</b>`);
        }
        return `${params[0]?.axisValueLabel} (${barYear.value})<br/>${lines.join('<br/>')}`;
      },
    },
    legend: legend(barSeries.value.map((s) => s.name)),
    grid: {
      top: '15%',
      left: '3%',
      right: '6%',
      bottom: stacked ? '28%' : '18%',
      containLabel: true,
    },
    xAxis: unitAxis(true),
    yAxis: {
      type: 'category' as const,
      data: categories,
      inverse: true,
      axisLabel: { width: 130, overflow: 'break' as const, fontSize: 11 },
    },
    series: barSeries.value.map((s) => ({
      name: s.name,
      type: 'bar',
      stack: 'total',
      barMaxWidth: 28,
      // A thin surface-colored edge leaves a gap between stacked segments
      itemStyle: { color: s.color, borderColor: SURFACE, borderWidth: 1 },
      data: s.values,
    })),
  };
});

const chartOption = computed(() =>
  !hasData.value ? {} : isBar.value ? barOption.value : lineOption.value,
);
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
