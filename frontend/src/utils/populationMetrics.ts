import type { YearData } from 'stores/leversStore';
import type { Region } from 'src/utils/region';

/**
 * Derived population-dynamics metrics for the Population tab.
 *
 * The model only outputs the total population ("lfs_population_total"). The
 * change and the growth rate are derived from it between consecutive years of
 * the output. The output is annual up to 2023 and then every 5 years, so both
 * are annualised over the gap: the value on a row describes the period ending
 * that year.
 */

export const POPULATION_FIELD = 'lfs_population_total';
export const POPULATION_CHANGE_FIELD = 'lfs_population_change';
export const POPULATION_GROWTH_RATE_FIELD = 'lfs_population_growth-rate';

/**
 * Returns a new countries object (rows copied, not mutated) augmented with the
 * annual population change (inhabitants per year) and the annual growth rate
 * (% per year). The first year has no previous year, so it gets neither.
 */
export function withPopulationMetrics(countries: { [key in Region]?: YearData[] }): {
  [key in Region]?: YearData[];
} {
  const result: { [key in Region]?: YearData[] } = {};

  Object.keys(countries).forEach((region) => {
    const rows = countries[region];
    if (!rows) return;

    result[region] = rows.map((row, index) => {
      const newRow: YearData = { ...row };
      const previous = rows[index - 1];
      const population = row[POPULATION_FIELD];
      const previousPopulation = previous?.[POPULATION_FIELD];
      const years = previous ? Number(row.year) - Number(previous.year) : 0;

      if (
        typeof population === 'number' &&
        typeof previousPopulation === 'number' &&
        previousPopulation > 0 &&
        years > 0
      ) {
        newRow[POPULATION_CHANGE_FIELD] = (population - previousPopulation) / years;
        newRow[POPULATION_GROWTH_RATE_FIELD] =
          ((population / previousPopulation) ** (1 / years) - 1) * 100;
      }
      return newRow;
    });
  });

  return result;
}
