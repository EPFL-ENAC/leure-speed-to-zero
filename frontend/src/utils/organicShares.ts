import type { YearData } from 'stores/leversStore';
import type { Region } from 'src/utils/region';

/**
 * Share of organic production for the Production tab's Crops and Livestock
 * sub-tabs.
 *
 * The crop, land-use and livestock modules do not return the organic split as
 * an output: it is their input, the "crop-share-organic" and "share-organic"
 * levers, applied to the cropland / production and to the herd. The
 * lever-data endpoint serves each lever's time series per lever position, so
 * withOrganicShares merges the position the user selected into the page's
 * rows, the same way the Diet page does for the energy requirement.
 */

// The levers serving the organic shares, one time series per lever position.
export const ORGANIC_SHARE_LEVERS = ['lever_crop-share-organic', 'lever_share-organic'];

// One row of the lever-data endpoint: a year plus one value per category
// ("agr_share_organic_<crop>[-]", "livestock_share-organic_<animal>[-]").
export type LeverSeriesRow = Record<string, number | string>;

export interface OrganicShareRows {
  region: string;
  // The rows of each lever at the position the user selected.
  rows: Record<string, LeverSeriesRow[]>;
}

/**
 * Returns a new countries object (rows copied, not mutated) augmented with the
 * organic shares (0-1) of the given region. Rows of any other region, or before
 * the lever series has loaded, are copied as they are.
 */
export function withOrganicShares(
  countries: { [key in Region]?: YearData[] },
  organicShares?: OrganicShareRows,
): { [key in Region]?: YearData[] } {
  const result: { [key in Region]?: YearData[] } = {};

  Object.keys(countries).forEach((region) => {
    const rows = countries[region];
    if (!rows) return;

    const sharesByYear = new Map<number, LeverSeriesRow[]>();
    if (region === organicShares?.region) {
      Object.values(organicShares.rows).forEach((leverRows) =>
        leverRows.forEach((r) => {
          const year = Number(r['Years']);
          sharesByYear.set(year, [...(sharesByYear.get(year) ?? []), r]);
        }),
      );
    }

    result[region] = rows.map((row) => {
      const newRow: YearData = { ...row };
      sharesByYear.get(Number(row.year))?.forEach((leverRow) => {
        Object.entries(leverRow).forEach(([key, value]) => {
          // "agr_share_organic_<crop>[-]" -> "agr_share_organic_<crop>"
          if (key !== 'Years' && key !== 'Country' && typeof value === 'number')
            newRow[key.replace(/\[.*\]$/, '')] = value;
        });
      });
      return newRow;
    });
  });

  return result;
}
