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
 *   SSR    = sum(production) / sum(demand) per group
 *
 * Categories without a domestic-production variable (seafood, animal by-products
 * such as fats/offal) are treated as 0 production, i.e. fully imported - a
 * reasonable default for Switzerland and transparent in the resulting charts.
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
    productionField: 'agr_domestic-production_afw_cereal',
  },
  {
    key: 'crop-fruit',
    demandField: 'agr_demand_crop-fruit',
    productionField: 'agr_domestic-production_afw_fruit',
  },
  {
    key: 'crop-oilcrop',
    demandField: 'agr_demand_crop-oilcrop',
    productionField: 'agr_domestic-production_afw_oilcrop',
  },
  {
    key: 'crop-pulse',
    demandField: 'agr_demand_crop-pulse',
    productionField: 'agr_domestic-production_afw_pulse',
  },
  {
    key: 'crop-rice',
    demandField: 'agr_demand_crop-rice',
    productionField: 'agr_domestic-production_afw_rice',
  },
  {
    key: 'crop-starch',
    demandField: 'agr_demand_crop-starch',
    productionField: 'agr_domestic-production_afw_starch',
  },
  {
    key: 'crop-veg',
    demandField: 'agr_demand_crop-veg',
    productionField: 'agr_domestic-production_afw_veg',
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
    demandField: 'agr_demand_pro-liv-meat-oth-animals',
    productionField: 'agr_domestic-production_afw_meat-oth-animals',
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
  { key: 'seafood-dfish', demandField: 'agr_demand_dfish', productionField: null },
  { key: 'seafood-ffish', demandField: 'agr_demand_ffish', productionField: null },
  {
    key: 'seafood-oth-aq-animals',
    demandField: 'agr_demand_oth-aq-animals',
    productionField: null,
  },
  { key: 'seafood-pfish', demandField: 'agr_demand_pfish', productionField: null },
  { key: 'seafood-seafood', demandField: 'agr_demand_seafood', productionField: null },
];

export const IMPORT_FIELD = (key: string) => `agr_import_${key}`;
export const EXPORT_FIELD = (key: string) => `agr_export_${key}`;
export const SSR_PLANT_FIELD = 'agr_ssr_plant-based';
export const SSR_ANIMAL_FIELD = 'agr_ssr_animal-based';

function augmentRow(row: YearData, categories: Category[]): { production: number; demand: number } {
  let productionSum = 0;
  let demandSum = 0;

  categories.forEach((category) => {
    const demand = row[category.demandField] ?? 0;
    const production = category.productionField ? (row[category.productionField] ?? 0) : 0;

    row[IMPORT_FIELD(category.key)] = Math.max(demand - production, 0);
    row[EXPORT_FIELD(category.key)] = Math.max(production - demand, 0);

    productionSum += production;
    demandSum += demand;
  });

  return { production: productionSum, demand: demandSum };
}

/**
 * Returns a new countries object (rows copied, not mutated) augmented with
 * per-category import/export fields and the plant/animal self-sufficiency
 * ratios, derived from the raw demand and domestic-production fields already
 * present on each row.
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
      const plant = augmentRow(newRow, PLANT_CATEGORIES);
      const animal = augmentRow(newRow, ANIMAL_CATEGORIES);

      newRow[SSR_PLANT_FIELD] = plant.demand > 0 ? (plant.production / plant.demand) * 100 : 0;
      newRow[SSR_ANIMAL_FIELD] = animal.demand > 0 ? (animal.production / animal.demand) * 100 : 0;

      return newRow;
    });
  });

  return result;
}
