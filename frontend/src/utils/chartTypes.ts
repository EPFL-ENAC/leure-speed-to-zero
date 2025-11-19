/**
 * Available chart types for data visualization
 *
 * These types can be used in chart configuration files (e.g., agriculture.json)
 * by setting the "type" field to one of these values.
 */
export type ChartType =
  | 'StackedArea' // Stacked area chart - shows composition over time
  | 'Line' // Line chart - shows trends over time
  | 'Bar' // Bar chart - compares values across categories
  | 'StackedBar' // Stacked bar chart - shows composition across categories
  | 'Sankey'; // Sankey diagram - shows flow relationships

/**
 * Configuration for series based on chart type
 */
export interface SeriesConfig {
  type: string;
  stack?: string;
  areaStyle?: object;
  symbol?: string;
  barWidth?: string;
}

/**
 * Maps a chart type string to its ECharts series configuration
 *
 * @param chartType - The chart type from the configuration (e.g., "StackedArea", "Line")
 * @returns ECharts series configuration object
 *
 * @example
 * ```typescript
 * const config = getSeriesConfig('StackedArea');
 * // Returns: { type: 'line', stack: 'total', areaStyle: {}, symbol: 'none' }
 * ```
 */
export function getSeriesConfig(chartType: string): SeriesConfig {
  const type = chartType as ChartType;

  switch (type) {
    case 'StackedArea':
      return {
        type: 'line',
        stack: 'total',
        areaStyle: {},
        symbol: 'none',
      };
    case 'Line':
      return {
        type: 'line',
        symbol: 'none',
      };
    case 'Bar':
      return {
        type: 'bar',
      };
    case 'StackedBar':
      return {
        type: 'bar',
        stack: 'total',
      };
    case 'Sankey':
      return {
        type: 'sankey',
      };
    default:
      // Fallback to line chart if unknown type
      return {
        type: 'line',
        symbol: 'none',
      };
  }
}
