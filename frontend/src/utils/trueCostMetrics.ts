import type { YearData } from 'stores/leversStore';
import type { Region } from 'src/utils/region';
import { POPULATION_FIELD } from 'src/utils/populationMetrics';

/**
 * Derived "cost saved vs business as usual" metrics for the True Cost tab.
 *
 * The model outputs the true cost of the selected pathway only. The saving is
 * the same output from the fixed "Business as usual (diet)" reference run minus
 * the current one, year by year: positive when the pathway costs less than BAU,
 * negative when it costs more.
 *
 * Health uses the residual cost (the net health burden left after the pathway),
 * which is what the Total chart stacks, so the two savings add up to the drop in
 * that chart's total.
 *
 * The per-capita metrics divide the same two costs by the population of the
 * same year. The costs are annual, so the result is CHF per capita per year.
 */

export const ENVIRONMENT_COST_FIELD = 'tcaf_lca_cost_total';
export const HEALTH_COST_FIELD = 'tcaf_health-diet_cost-residual_total';
export const ENVIRONMENT_SAVED_FIELD = 'tcaf_lca_cost-saved_total';
export const HEALTH_SAVED_FIELD = 'tcaf_health-diet_cost-saved_total';

export const ENVIRONMENT_PER_CAPITA_FIELD = 'tcaf_lca_cost-per-cap_total';
export const HEALTH_PER_CAPITA_FIELD = 'tcaf_health-diet_cost-residual-per-cap_total';

const SAVED_FIELDS: Array<[cost: string, saved: string]> = [
  [ENVIRONMENT_COST_FIELD, ENVIRONMENT_SAVED_FIELD],
  [HEALTH_COST_FIELD, HEALTH_SAVED_FIELD],
];

/**
 * Returns a new countries object (rows copied, not mutated) augmented with the
 * cost saved against the BAU reference for the environment and for health.
 * Rows are matched by year. A row with no BAU counterpart, or a region without
 * a reference, gets no saving rather than a misleading zero.
 */
export function withTrueCostSavings(
  countries: { [key in Region]?: YearData[] },
  bauCountries: { [key in Region]?: YearData[] } | undefined,
): { [key in Region]?: YearData[] } {
  const result: { [key in Region]?: YearData[] } = {};

  Object.keys(countries).forEach((region) => {
    const rows = countries[region];
    if (!rows) return;

    const bauByYear = new Map<number, YearData>();
    bauCountries?.[region]?.forEach((row) => bauByYear.set(Number(row.year), row));

    result[region] = rows.map((row) => {
      const newRow: YearData = { ...row };
      const bauRow = bauByYear.get(Number(row.year));
      if (!bauRow) return newRow;

      SAVED_FIELDS.forEach(([costField, savedField]) => {
        const bauCost = bauRow[costField];
        const cost = row[costField];
        if (typeof bauCost === 'number' && typeof cost === 'number') {
          newRow[savedField] = bauCost - cost;
        }
      });
      return newRow;
    });
  });

  return result;
}

const PER_CAPITA_FIELDS: Array<[cost: string, perCapita: string]> = [
  [ENVIRONMENT_COST_FIELD, ENVIRONMENT_PER_CAPITA_FIELD],
  [HEALTH_COST_FIELD, HEALTH_PER_CAPITA_FIELD],
];

/**
 * Returns a new countries object (rows copied, not mutated) augmented with the
 * environmental and residual health costs per capita per year. A row with no
 * positive population gets no per-capita value rather than a misleading zero.
 */
export function withTrueCostPerCapita(countries: { [key in Region]?: YearData[] }): {
  [key in Region]?: YearData[];
} {
  const result: { [key in Region]?: YearData[] } = {};

  Object.keys(countries).forEach((region) => {
    const rows = countries[region];
    if (!rows) return;

    result[region] = rows.map((row) => {
      const newRow: YearData = { ...row };
      const population = row[POPULATION_FIELD];
      if (typeof population !== 'number' || population <= 0) return newRow;

      PER_CAPITA_FIELDS.forEach(([costField, perCapitaField]) => {
        const cost = row[costField];
        if (typeof cost === 'number') newRow[perCapitaField] = cost / population;
      });
      return newRow;
    });
  });

  return result;
}
