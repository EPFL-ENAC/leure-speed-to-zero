import type { ChartConfig, OutputConfig, SectorData, YearData } from 'stores/leversStore';
import type { Region } from 'src/utils/region';
import type { TranslationObject } from 'src/utils/translationHelpers';
import { withDietMetrics } from 'src/utils/dietMetrics';
import { withTrueCostPerCapita, withTrueCostSavings } from 'src/utils/trueCostMetrics';

/**
 * The eight TCAF diet pathways the Pathway comparison tab puts side by side:
 * four diets (business as usual, the current 2023 diet, the Swiss food pyramid
 * and the planetary health diet), each with the current food waste and with low
 * waste. They differ in five levers only (diet adherence, diet split, food
 * waste, crop losses and livestock losses), everything else is business as usual.
 *
 * "title" is the pathway's title in ExamplePathways, the key its levers are read
 * by. "label" is the short name the charts show. A diet keeps its color; the
 * low-waste variant is told apart by a dashed line, so color is never the only cue.
 */
export interface ComparisonPathway {
  title: string;
  label: TranslationObject;
  color: string;
  lowWaste: boolean;
}

// The four diets, each run with the current food waste and with low waste
const DIETS: Array<{ title: string; label: TranslationObject; color: string }> = [
  {
    title: 'Business as usual (diet)',
    label: { enUS: 'Business as usual', frFR: 'Scénario tendanciel', deDE: 'Trendszenario' },
    color: '#eb6834',
  },
  {
    title: 'Current diet',
    label: { enUS: 'Current diet', frFR: 'Alimentation actuelle', deDE: 'Aktuelle Ernährung' },
    color: '#8e5bd0',
  },
  {
    title: 'Swiss food pyramid',
    label: {
      enUS: 'Swiss food pyramid',
      frFR: 'Pyramide alimentaire suisse',
      deDE: 'Schweizer Lebensmittelpyramide',
    },
    color: '#2a78d6',
  },
  {
    title: 'Planetary health diet (EAT-Lancet 2025)',
    label: {
      enUS: 'Planetary health diet',
      frFR: 'Régime de santé planétaire',
      deDE: 'Planetary Health Diet',
    },
    color: '#1baf7a',
  },
];

const LOW_WASTE_SUFFIX: TranslationObject = {
  enUS: ' + low waste',
  frFR: ' + gaspillage réduit',
  deDE: ' + weniger Verschwendung',
};

export const COMPARISON_PATHWAYS: ComparisonPathway[] = [
  ...DIETS.map((diet) => ({ ...diet, lowWaste: false })),
  ...DIETS.map((diet) => ({
    title: `${diet.title} - low waste`,
    label: {
      enUS: diet.label.enUS + LOW_WASTE_SUFFIX.enUS,
      frFR: diet.label.frFR + LOW_WASTE_SUFFIX.frFR,
      deDE: diet.label.deDE + LOW_WASTE_SUFFIX.deDE,
    },
    color: diet.color,
    lowWaste: true,
  })),
];

// The reference every "saved" value is measured against: same run as the
// True Cost tab, the first of the eight.
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
  unit: string | TranslationObject;
  scale?: number;
  fromYear?: number;
  year?: number;
  outputs: Array<string | OutputConfig>;
  groups?: ChartConfig['groups'];
}

/**
 * Builds the eight runs the charts read from the model results of each pathway,
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
