import type { ChartConfig, OutputConfig, SectorData, YearData } from 'stores/leversStore';
import type { Region } from 'src/utils/region';
import type { TranslationObject } from 'src/utils/translationHelpers';
import { withDietMetrics } from 'src/utils/dietMetrics';
import { withTrueCostPerCapita, withTrueCostSavings } from 'src/utils/trueCostMetrics';

/**
 * The seven TCAF diet pathways the Pathway comparison tab puts side by side:
 * three diets, each with the current food waste and with low waste, and the
 * current (2023) diet, with the current food waste only. They differ
 * in five levers only (diet adherence, diet split, food waste, crop losses and
 * livestock losses), everything else is business as usual.
 *
 * "title" is the pathway's title in ExamplePathways, the key its levers are read
 * by. "label" is the short name the charts show. A diet keeps its color; the
 * low-waste variant is told apart by a dashed line, so color is never the only cue.
 */
export interface ComparisonPathway {
  title: string;
  label: string;
  color: string;
  lowWaste: boolean;
}

export const COMPARISON_PATHWAYS: ComparisonPathway[] = [
  {
    title: 'Business as usual (diet)',
    label: 'Business as usual',
    color: '#eb6834',
    lowWaste: false,
  },
  { title: 'Current diet', label: 'Current diet', color: '#8e5bd0', lowWaste: false },
  { title: 'Swiss food pyramid', label: 'Swiss food pyramid', color: '#2a78d6', lowWaste: false },
  {
    title: 'Planetary health diet (EAT-Lancet 2025)',
    label: 'Planetary health diet',
    color: '#1baf7a',
    lowWaste: false,
  },
  {
    title: 'Business as usual (diet) - low waste',
    label: 'Business as usual + low waste',
    color: '#eb6834',
    lowWaste: true,
  },
  {
    title: 'Swiss food pyramid - low waste',
    label: 'Swiss food pyramid + low waste',
    color: '#2a78d6',
    lowWaste: true,
  },
  {
    title: 'Planetary health diet (EAT-Lancet 2025) - low waste',
    label: 'Planetary health diet + low waste',
    color: '#1baf7a',
    lowWaste: true,
  },
];

// The reference every "saved" value is measured against: same run as the
// True Cost tab, the first of the seven.
const BAU_TITLE = 'Business as usual (diet)';

// One pathway's model results for the current region, derived metrics included.
export interface PathwayRun {
  pathway: ComparisonPathway;
  rows: YearData[];
}

/**
 * A chart of the comparison tab. Both types plot one value per pathway:
 * - PathwayLine: the first output over time, one line per pathway, from "fromYear"
 *   (the pathways are identical until the transition, so the earlier years only
 *   flatten the picture).
 * - PathwayBar: the outputs (or the sum of each group's outputs) stacked into one
 *   bar per pathway, read at "year" (2050 by default).
 */
export interface PathwayChartConfig {
  title: string | TranslationObject;
  type: 'PathwayLine' | 'PathwayBar';
  unit: string;
  scale?: number;
  fromYear?: number;
  year?: number;
  outputs: Array<string | OutputConfig>;
  groups?: ChartConfig['groups'];
}

/**
 * Builds the seven runs the charts read from the model results of each pathway,
 * keyed by pathway title. A pathway with no results yet is left out. The cost
 * saved is measured against the BAU run and the cost per capita against each
 * run's own population.
 */
export function buildPathwayRuns(
  results: Record<string, SectorData>,
  region: Region,
): PathwayRun[] {
  const bauCountries = results[BAU_TITLE]?.countries;

  return COMPARISON_PATHWAYS.flatMap((pathway) => {
    const countries = results[pathway.title]?.countries;
    if (!countries) return [];

    const derived = withTrueCostPerCapita(
      withTrueCostSavings(withDietMetrics(countries), bauCountries),
    );
    const rows = derived[region];
    return rows ? [{ pathway, rows }] : [];
  });
}
