import type { YearData } from 'stores/leversStore';
import type { Region } from 'src/utils/region';

/**
 * Derived diet-intake and food-waste metrics for the Dietary habits tab.
 *
 * The model outputs, per food category, the food demand in kcal
 * ("agr_demand_<cat>", intake + waste), that same demand in tonnes
 * ("agr_demand_tpe_<cat>") and the food waste in tonnes
 * ("lfs_food-wastes_tpe_<cat>"). Intake in tonnes plus waste in tonnes
 * equals the demand in tonnes, and a category's kcal per tonne is fixed, so:
 *   waste ratio = waste (t) / demand (t)
 *   intake (kcal) = demand (kcal) * (1 - waste ratio)
 * Intake is then divided by the population and by 365.25 days (the model's own
 * convention) to get kcal per capita per day.
 *
 * The individual energy requirement (by sex and age group) is not a model
 * output but the model's "kcal-req" lever input, served per lever position by
 * the lever-data endpoint; withDietMetrics merges the selected position in.
 */

// One row of the lever-data endpoint: a year plus one value per sex-age group
// ("agr_kcal-req_<sex>-<age>[kcal/cap/day]").
export type EnergyRequirementRow = Record<string, number | string>;

// Same food groups (and same members) as the "groups" of the DietBauVsTarget
// chart in config/subtabs/dietary-habits.json.
export const FOOD_GROUPS: Record<string, string[]> = {
  'cereals-starches': ['crop-cereal', 'crop-rice', 'crop-starch'],
  'fruit-veg': ['crop-fruit', 'crop-veg'],
  'oilcrops-pulses': ['crop-oilcrop', 'crop-pulse'],
  'dairy-eggs': ['pro-liv-abp-dairy-milk', 'pro-liv-abp-hens-egg'],
  meat: [
    'pro-liv-abp-processed-afat',
    'pro-liv-abp-processed-offal',
    'pro-liv-meat-bovine',
    'pro-liv-meat-oth-animal',
    'pro-liv-meat-pig',
    'pro-liv-meat-poultry',
    'pro-liv-meat-sheep',
  ],
  seafood: [
    'seafood-dfish',
    'seafood-ffish',
    'seafood-oth-aq-animal',
    'seafood-pfish',
    'seafood-seafood',
  ],
  beverages: ['pro-bev-beer', 'pro-bev-bev-alc', 'pro-bev-bev-fer', 'pro-bev-wine'],
  'sweeteners-stimulants': [
    'pro-crop-processed-sugar',
    'pro-crop-processed-sweet',
    'pro-crop-processed-voil',
    'stm-cocoa',
    'stm-coffee',
    'stm-tea',
  ],
};

const DAYS_PER_YEAR = 365.25;

// Processed food shares (%) of the Processed food sub-tab. The diet module
// outputs the processed meat ("pro-liv-meat-processed") and the whole cereals
// ("crop-cereal-whole") in g/cap/day as parts of the meat and cereal totals,
// not as extra categories: the model computes them as total * (1 - unprocessed
// share) and cereal * whole share. The shares are therefore the ratio to those
// totals, and the other side of each split is the remainder.
const MEAT_CATEGORIES = [
  'pro-liv-meat-bovine',
  'pro-liv-meat-oth-animal',
  'pro-liv-meat-pig',
  'pro-liv-meat-poultry',
  'pro-liv-meat-sheep',
];
const CONSUMED_FIELD = (category: string) => `lfs_consumers-diet_${category}`;
export const MEAT_SHARE_FIELD = (kind: 'processed' | 'unprocessed') => `diet-share_meat-${kind}`;
export const CEREAL_SHARE_FIELD = (kind: 'whole' | 'refined') => `diet-share_cereal-${kind}`;

export const DIET_INTAKE_FIELD = (category: string) => `diet-intake_${category}`;
export const FOOD_WASTE_FIELD = (group: string) => `food-waste_${group}`;
// Waste ratio (%), per food group and per individual category
export const FOOD_WASTE_RATIO_FIELD = (groupOrCategory: string) =>
  `food-waste-ratio_${groupOrCategory}`;

const DEMAND_KCAL_FIELD = (category: string) => `agr_demand_${category}`;
const DEMAND_TONNES_FIELD = (category: string) => `agr_demand_tpe_${category}`;
const WASTE_TONNES_FIELD = (category: string) => `lfs_food-wastes_tpe_${category}`;

function num(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

function augmentRow(row: YearData): void {
  // Only the regions the dietary-habits sector ran for carry the diet outputs
  if (!(DEMAND_TONNES_FIELD('crop-cereal') in row)) return;

  const population = num(row['lfs_population_total']);

  Object.entries(FOOD_GROUPS).forEach(([group, categories]) => {
    let groupWaste = 0;
    let groupDemand = 0;

    categories.forEach((category) => {
      const demandTonnes = num(row[DEMAND_TONNES_FIELD(category)]);
      const wasteTonnes = num(row[WASTE_TONNES_FIELD(category)]);
      groupWaste += wasteTonnes;
      groupDemand += demandTonnes;

      if (demandTonnes > 0) {
        row[FOOD_WASTE_RATIO_FIELD(category)] = (wasteTonnes / demandTonnes) * 100;
      }

      if (population > 0 && demandTonnes > 0) {
        const intakeKcal = num(row[DEMAND_KCAL_FIELD(category)]) * (1 - wasteTonnes / demandTonnes);
        row[DIET_INTAKE_FIELD(category)] = intakeKcal / population / DAYS_PER_YEAR;
      }
    });

    row[FOOD_WASTE_FIELD(group)] = groupWaste;
    if (groupDemand > 0) {
      row[FOOD_WASTE_RATIO_FIELD(group)] = (groupWaste / groupDemand) * 100;
    }
  });
}

function augmentProcessedShares(row: YearData): void {
  const totalMeat = MEAT_CATEGORIES.reduce((sum, c) => sum + num(row[CONSUMED_FIELD(c)]), 0);
  const processedMeat = num(row[CONSUMED_FIELD('pro-liv-meat-processed')]);
  if (totalMeat > 0 && CONSUMED_FIELD('pro-liv-meat-processed') in row) {
    const processed = Math.min(processedMeat / totalMeat, 1) * 100;
    row[MEAT_SHARE_FIELD('processed')] = processed;
    row[MEAT_SHARE_FIELD('unprocessed')] = 100 - processed;
  }

  const cereal = num(row[CONSUMED_FIELD('crop-cereal')]);
  if (cereal > 0 && CONSUMED_FIELD('crop-cereal-whole') in row) {
    const whole = Math.min(num(row[CONSUMED_FIELD('crop-cereal-whole')]) / cereal, 1) * 100;
    row[CEREAL_SHARE_FIELD('whole')] = whole;
    row[CEREAL_SHARE_FIELD('refined')] = 100 - whole;
  }
}

/**
 * Returns a new countries object (rows copied, not mutated) augmented with the
 * per-category diet intake and waste ratio, the per-group food waste and waste ratio, the
 * processed meat and whole cereal shares, and the energy requirement of the given
 * region. Rows without the diet outputs are copied as they are.
 */
export function withDietMetrics(
  countries: { [key in Region]?: YearData[] },
  energyRequirement?: { region: string; rows: EnergyRequirementRow[] },
): {
  [key in Region]?: YearData[];
} {
  const result: { [key in Region]?: YearData[] } = {};

  Object.keys(countries).forEach((region) => {
    const rows = countries[region];
    if (!rows) return;

    const requirementByYear = new Map<number, EnergyRequirementRow>();
    if (region === energyRequirement?.region) {
      energyRequirement.rows.forEach((r) => requirementByYear.set(Number(r['Years']), r));
    }

    result[region] = rows.map((row) => {
      const newRow: YearData = { ...row };
      augmentRow(newRow);
      augmentProcessedShares(newRow);
      Object.entries(requirementByYear.get(Number(row.year)) ?? {}).forEach(([key, value]) => {
        // "agr_kcal-req_<group>[kcal/cap/day]" -> "agr_kcal-req_<group>"
        if (key.startsWith('agr_kcal-req_') && typeof value === 'number')
          newRow[key.replace(/\[.*\]$/, '')] = value;
      });
      return newRow;
    });
  });

  return result;
}
