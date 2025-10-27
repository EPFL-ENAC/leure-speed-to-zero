export interface DifficultyArea {
  min: number;
  max: number;
  color: string;
  label: string;
}

export interface UntranslatedLever {
  code: string;
  range: (string | number)[];
  type: string;
  disabled?: boolean;
  difficultyColors: DifficultyArea[];
}

export interface Lever {
  code: string;
  title: string;
  group: string;
  headline: string;
  popupText?: string;
  disabled?: boolean;
  range: (string | number)[];
  type: string;
  difficultyColors: DifficultyArea[];
}

export const sectors = [
  {
    code: 'Buildings',
    levers: [
      'lever_heatcool-behaviour',
      'lever_floor-intensity',
      'lever_building-renovation-rate',
      'lever_heating-technology-fuel',
      'lever_heating-efficiency',
      'lever_appliance-own',
      'lever_appliance-use',
      'lever_appliance-efficiency',
    ],
  },
  {
    code: 'Transport',
    levers: [
      'lever_pkm',
      'lever_passenger_aviation-pkm',
      'lever_passenger_modal-share',
      'lever_passenger_occupancy',
      'lever_passenger_utilization-rate',
      'lever_fuel-mix',
      'lever_passenger_technology-share_new',
      'lever_passenger_veh-efficiency_new',
      'lever_freight_modal-share',
      'lever_freight_technology-share_new',
      'lever_freight_tkm',
      'lever_freight_utilization-rate',
      'lever_freight_vehicle-efficiency_new',
    ],
  },
  {
    code: 'Behaviours',
    levers: [
      'lever_kcal-req',
      'lever_diet',
      'lever_fwaste',
      'lever_floor-intensity',
      'lever_heatcool-behaviour',
      'lever_appliance-own',
      'lever_appliance-use',
      'lever_paperpack',
      'lever_product-substitution-rate',
      'lever_passenger_aviation-pkm',
      'lever_passenger_modal-share',
      'lever_passenger_occupancy',
      'lever_passenger_utilization-rate',
      'lever_pkm',
    ],
  },
  { code: 'Forestry', levers: ['lever_harvest-rate'] },
  {
    code: 'Industry',
    levers: [
      'lever_paperpack',
      'lever_product-substitution-rate',
      'lever_material-efficiency',
      'lever_material-switch',
      'lever_technology-share',
      'lever_technology-development',
      'lever_energy-carrier-mix',
      'lever_lca-material-decomp',
    ],
  },
  {
    code: 'Agriculture',
    levers: [
      'lever_kcal-req',
      'lever_diet',
      'lever_fwaste',
      'lever_climate-smart-crop',
      'lever_climate-smart-livestock',
      'lever_bioenergy-capacity',
      'lever_alt-protein',
      'lever_biomass-hierarchy',
    ],
  },
  { code: 'Boundary conditions', levers: ['lever_pop', 'lever_temp'] },
];

export function getAllTranslatedLevers(t: (key: string) => string): Lever[] {
  return levers.map((lever) => getTranslatedLeverData(lever.code, t));
}

// Helper function to get translated lever
export function getTranslatedLeverData(leverCode: string, t: (key: string) => string): Lever {
  const translationKey = `lever.${leverCode}`;

  // Check if translation exists
  const titleKey = `${translationKey}.title`;
  const groupKey = `${translationKey}.group`;
  const headlineKey = `${translationKey}.headline`;
  const popupTextKey = `${translationKey}.popupText`;
  const untranslatedLever = levers.find((lever) => lever.code === leverCode) as UntranslatedLever;

  const difficultyColors = untranslatedLever.difficultyColors.map((area) => ({
    ...area,
    label: t(area.label),
  }));

  return {
    title: t(titleKey),
    group: t(groupKey),
    popupText: t(popupTextKey),
    headline: t(headlineKey),
    ...untranslatedLever,
    difficultyColors: difficultyColors,
  };
}

export const levers: UntranslatedLever[] = [
  {
    code: 'lever_pkm',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_passenger_modal-share',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_passenger_occupancy',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_passenger_utilization-rate',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_floor-intensity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_floor-area-fraction',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_heatcool-behaviour',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_appliance-own',
    range: [1, 2, 3, 4],
    type: 'num',
    disabled: true,
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_appliance-use',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_kcal-req',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_diet',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_paperpack',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_product-substitution-rate',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_fwaste',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_freight_tkm',
    range: [1, 2, 3, 4],
    type: 'num',
    disabled: true,
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_passenger_veh-efficiency_new',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_passenger_technology-share_new',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_freight_vehicle-efficiency_new',
    range: [1, 2, 3, 4],
    type: 'num',
    disabled: true,
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_freight_technology-share_new',
    range: [1, 2, 3, 4],
    type: 'num',
    disabled: true,
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_freight_modal-share',
    range: [1, 2, 3, 4],
    type: 'num',
    disabled: true,
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_freight_utilization-rate',
    range: [1, 2, 3, 4],
    type: 'num',
    disabled: true,
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_fuel-mix',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_building-renovation-rate',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#559ADE', label: 'lever.difficulty.hard' },
    ],
  },
  {
    code: 'lever_district-heating-share',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_heating-technology-fuel',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_heating-efficiency',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_appliance-efficiency',
    range: [1, 2, 3, 4],
    disabled: true,
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_material-efficiency',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_material-switch',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_technology-share',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_technology-development',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_energy-carrier-mix',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_cc',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_ccus',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_decom_fossil',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_ccs',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_capacity_nuclear',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_capacity_RES_wind',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_capacity_RES_solar',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_capacity_RES_other',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_bal-strat',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_str_charging',
    range: ['A', 'B', 'C', 'D'],
    type: 'char',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_climate-smart-crop',
    range: ['A', 'B', 'C', 'D'],
    type: 'char',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_climate-smart-livestock',
    range: ['A', 'B', 'C', 'D'],
    type: 'char',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_bioenergy-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_alt-protein',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_climate-smart-forestry',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_land-man',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_biomass-hierarchy',
    range: ['A', 'B', 'C', 'D'],
    type: 'char',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_biodiversity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_land-prioritisation',
    range: ['A', 'B'],
    type: 'char',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_pop',
    range: ['A', 'B', 'C', 'D'],
    type: 'char',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_urbpop',
    range: ['A', 'B', 'C', 'D'],
    type: 'char',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_ems-after-2050',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_food-net-import',
    range: ['A', 'B', 'C', 'D'],
    type: 'char',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_product-net-import',
    range: ['A', 'B', 'C', 'D'],
    type: 'char',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_material-net-import',
    range: ['A', 'B', 'C', 'D'],
    type: 'char',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_temp',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_passenger_aviation-pkm',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_pv-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_csp-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_onshore-wind-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_offshore-wind-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_biogas-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_biomass-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_hydroelectric-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_geothermal-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_marine-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_gas-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_oil-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_coal-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_nuclear-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_carbon-storage-capacity',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_ev-charging-profile',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_non-residential-heat-profile',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_residential-heat-profile',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_non-residential-cooling-profile',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_residential-cooling-profile',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_eol-waste-management',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_eol-material-recovery',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
  {
    code: 'lever_harvest-rate',
    range: [1, 2, 3, 4],
    type: 'num',
    difficultyColors: [
      { min: 1, max: 1, color: '#CFE3F7', label: 'lever.difficulty.easy' },
      { min: 2, max: 2, color: '#92BFEB', label: 'lever.difficulty.moderate' },
      { min: 3, max: 3, color: '#559ADE', label: 'lever.difficulty.hard' },
      { min: 4, max: 4, color: '#1876D2', label: 'lever.difficulty.ambitious' },
    ],
  },
];
