import type { YearData } from 'stores/leversStore';
import type { Region } from 'src/utils/region';

/**
 * Derived livestock productivity for the Production tab's Livestock sub-tab.
 *
 * The livestock module outputs the herd (livestock units, "lsu") and the
 * domestic production (kcal) of each animal category separately. The
 * productivity is the second divided by the first: the kcal a livestock unit
 * of that category yields per year. A row where the herd is missing or not
 * positive gets no value rather than a misleading zero.
 */

const LIVESTOCK_CATEGORIES = [
  'abp-dairy-milk',
  'abp-hens-egg',
  'meat-bovine',
  'meat-oth-animal',
  'meat-pig',
  'meat-poultry',
  'meat-sheep',
];

export const LIVESTOCK_POPULATION_FIELD = (key: string) => `agr_liv_population_${key}`;
export const LIVESTOCK_PRODUCTION_FIELD = (key: string) => `agr_domestic-production_afw_${key}`;
export const LIVESTOCK_PRODUCTIVITY_FIELD = (key: string) => `agr_liv_productivity_${key}`;

/**
 * Returns a new countries object (rows copied, not mutated) augmented with the
 * domestic production per livestock unit of each animal category.
 */
export function withLivestockMetrics(countries: { [key in Region]?: YearData[] }): {
  [key in Region]?: YearData[];
} {
  const result: { [key in Region]?: YearData[] } = {};

  Object.keys(countries).forEach((region) => {
    const rows = countries[region];
    if (!rows) return;

    result[region] = rows.map((row) => {
      const newRow: YearData = { ...row };

      LIVESTOCK_CATEGORIES.forEach((key) => {
        const population = row[LIVESTOCK_POPULATION_FIELD(key)];
        const production = row[LIVESTOCK_PRODUCTION_FIELD(key)];
        if (typeof population === 'number' && population > 0 && typeof production === 'number') {
          newRow[LIVESTOCK_PRODUCTIVITY_FIELD(key)] = production / population;
        }
      });
      return newRow;
    });
  });

  return result;
}
