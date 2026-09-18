import type { YearData } from 'stores/leversStore';
import type { Region } from 'src/utils/region';

/**
 * Derived import/export/self-sufficiency metrics for the Production tab.
 *
 * The model does not expose separate import/export flows or a self-sufficiency
 * ratio as output variables (only domestic production and total demand). These
 * are the standard trade-balance identities computed from those two:
 *   import = max(demand - production, 0)
 *   export = max(production - demand, 0)
 *   SSR    = production / demand, per category
 *
 * Demand comes from the "dietary-habits" sector and production from "crop"
 * (plant categories) and "livestock" (meat/dairy/eggs) - all three react to
 * the diet/self-sufficiency levers, unlike the legacy "agriculture" sector
 * (see leversStore.ts's getSectorDataWithKpis), which must never be used here.
 *
 * Seafood and animal by-products (offal/fats) have no domestic-production
 * variable exposed by the model at all, so they are treated as 0 production,
 * i.e. fully imported - a reasonable default for Switzerland.
 */

interface Category {
  key: string;
  demandField: string;
  productionField: string | null;
}

export const PLANT_CATEGORIES: Category[] = [
  {
    key: 'crop-cereal',
    demandField: 'agr_demand_crop-cereal',
    productionField: 'agr_domestic-production_afw_crop-cereal',
  },
  {
    key: 'crop-fruit',
    demandField: 'agr_demand_crop-fruit',
    productionField: 'agr_domestic-production_afw_crop-fruit',
  },
  {
    key: 'crop-oilcrop',
    demandField: 'agr_demand_crop-oilcrop',
    productionField: 'agr_domestic-production_afw_crop-oilcrop',
  },
  {
    key: 'crop-pulse',
    demandField: 'agr_demand_crop-pulse',
    productionField: 'agr_domestic-production_afw_crop-pulse',
  },
  {
    key: 'crop-rice',
    demandField: 'agr_demand_crop-rice',
    productionField: 'agr_domestic-production_afw_crop-rice',
  },
  {
    key: 'crop-starch',
    demandField: 'agr_demand_crop-starch',
    productionField: 'agr_domestic-production_afw_crop-starch',
  },
  {
    key: 'crop-veg',
    demandField: 'agr_demand_crop-veg',
    productionField: 'agr_domestic-production_afw_crop-veg',
  },
];

export const ANIMAL_CATEGORIES: Category[] = [
  {
    key: 'pro-liv-abp-dairy-milk',
    demandField: 'agr_demand_pro-liv-abp-dairy-milk',
    productionField: 'agr_domestic-production_afw_abp-dairy-milk',
  },
  {
    key: 'pro-liv-abp-hens-egg',
    demandField: 'agr_demand_pro-liv-abp-hens-egg',
    productionField: 'agr_domestic-production_afw_abp-hens-egg',
  },
  {
    key: 'pro-liv-abp-processed-afat',
    demandField: 'agr_demand_pro-liv-abp-processed-afat',
    productionField: null,
  },
  {
    key: 'pro-liv-abp-processed-offal',
    demandField: 'agr_demand_pro-liv-abp-processed-offal',
    productionField: null,
  },
  {
    key: 'pro-liv-meat-bovine',
    demandField: 'agr_demand_pro-liv-meat-bovine',
    productionField: 'agr_domestic-production_afw_meat-bovine',
  },
  {
    key: 'pro-liv-meat-oth-animals',
    demandField: 'agr_demand_pro-liv-meat-oth-animal',
    productionField: 'agr_domestic-production_afw_meat-oth-animal',
  },
  {
    key: 'pro-liv-meat-pig',
    demandField: 'agr_demand_pro-liv-meat-pig',
    productionField: 'agr_domestic-production_afw_meat-pig',
  },
  {
    key: 'pro-liv-meat-poultry',
    demandField: 'agr_demand_pro-liv-meat-poultry',
    productionField: 'agr_domestic-production_afw_meat-poultry',
  },
  {
    key: 'pro-liv-meat-sheep',
    demandField: 'agr_demand_pro-liv-meat-sheep',
    productionField: 'agr_domestic-production_afw_meat-sheep',
  },
  { key: 'seafood-dfish', demandField: 'agr_demand_seafood-dfish', productionField: null },
  { key: 'seafood-ffish', demandField: 'agr_demand_seafood-ffish', productionField: null },
  {
    key: 'seafood-oth-aq-animals',
    demandField: 'agr_demand_seafood-oth-aq-animal',
    productionField: null,
  },
  { key: 'seafood-pfish', demandField: 'agr_demand_seafood-pfish', productionField: null },
  { key: 'seafood-seafood', demandField: 'agr_demand_seafood-seafood', productionField: null },
];

export const IMPORT_FIELD = (key: string) => `agr_import_${key}`;
export const EXPORT_FIELD = (key: string) => `agr_export_${key}`;
// Distinct from the model's own raw "agr_ssr_<category>" fields (crop sector's
// lever-target ratio) - this is the derived production/demand ratio.
export const SSR_RATIO_FIELD = (key: string) => `agr_ssr-ratio_${key}`;

function categoryRatio(row: YearData, category: Category): number {
  const demand = row[category.demandField] ?? 0;
  const production = category.productionField ? (row[category.productionField] ?? 0) : 0;
  return demand > 0 ? production / demand : 0;
}

function augmentRow(row: YearData, categories: Category[]): void {
  categories.forEach((category) => {
    const demand = row[category.demandField] ?? 0;
    const production = category.productionField ? (row[category.productionField] ?? 0) : 0;

    row[IMPORT_FIELD(category.key)] = Math.max(demand - production, 0);
    row[EXPORT_FIELD(category.key)] = Math.max(production - demand, 0);
    row[SSR_RATIO_FIELD(category.key)] = categoryRatio(row, category) * 100;
  });
}

/**
 * Returns a new countries object (rows copied, not mutated) augmented with
 * per-category import/export fields and self-sufficiency ratios, derived from
 * the raw demand and domestic-production fields already present on each row.
 */
export function withSelfSufficiencyMetrics(countries: { [key in Region]?: YearData[] }): {
  [key in Region]?: YearData[];
} {
  const result: { [key in Region]?: YearData[] } = {};

  Object.keys(countries).forEach((region) => {
    const rows = countries[region];
    if (!rows) return;

    result[region] = rows.map((row) => {
      const newRow: YearData = { ...row };
      augmentRow(newRow, PLANT_CATEGORIES);
      augmentRow(newRow, ANIMAL_CATEGORIES);

      return newRow;
    });
  });

  return result;
}
