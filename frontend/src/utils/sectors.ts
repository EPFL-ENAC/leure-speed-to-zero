export interface Sector {
  label: string;
  value: string;
  icon: string;
  disabled?: boolean;
}

export const sectors: Sector[] = [
  { label: 'Buildings', value: 'buildings', icon: 'apartment' },
  { label: 'Transport', value: 'transport', icon: 'bike_scooter' },
  { label: 'Forestry', value: 'forestry', icon: 'forest' },
  { label: 'Agriculture', value: 'agriculture', icon: 'agriculture', disabled: true },
  { label: 'Overall', value: 'overall', icon: 'dashboard', disabled: true },
  // Theses ones are examples of sectors that can be added later
  // Icons can be found in Material Icons or similar icon libraries like :
  //   https://fonts.google.com/icons?icon.set=Material+Icons
  // https://pictogrammers.com/library/mdi/
  //   { label: 'Waste', value: 'waste', icon: 'delete' },
  //   { label: 'Energy', value: 'energy', icon: 'solar_power' },
  //   { label: 'Industry', value: 'industry', icon: 'factory' },
  //   { label: 'Water', value: 'water', icon: 'water_drop' },
  //   { label: 'Mining', value: 'mining', icon: 'hardware' },
  //   { label: 'Tourism', value: 'tourism', icon: 'luggage' },
  //   { label: 'Healthcare', value: 'healthcare', icon: 'local_hospital' },
  //   { label: 'Education', value: 'education', icon: 'school' },
  //   { label: 'Finance', value: 'finance', icon: 'account_balance' },
  //   { label: 'Retail', value: 'retail', icon: 'shopping_cart' },
  //   { label: 'Technology', value: 'technology', icon: 'computer' },
  //   { label: 'Aviation', value: 'aviation', icon: 'flight' },
  //   { label: 'Shipping', value: 'shipping', icon: 'directions_boat' },
  //   { label: 'Construction', value: 'construction', icon: 'construction' },
  //   { label: 'Textiles', value: 'textiles', icon: 'dry_cleaning' },
  //   { label: 'Food Processing', value: 'food-processing', icon: 'restaurant' },
  //   { label: 'Pharmaceuticals', value: 'pharmaceuticals', icon: 'medication' },
  //   { label: 'Chemicals', value: 'chemicals', icon: 'science' },
  //   { label: 'Paper & Pulp', value: 'paper-pulp', icon: 'description' },
  //   { label: 'Steel & Metals', value: 'steel-metals', icon: 'build' },
  //   { label: 'Cement', value: 'cement', icon: 'concrete' },
  //   { label: 'Telecommunications', value: 'telecommunications', icon: 'cell_tower' },
  //   { label: 'Entertainment', value: 'entertainment', icon: 'theaters' },
  //   { label: 'Sports', value: 'sports', icon: 'sports_soccer' },
];

export interface KPIConfig {
  name: string;
  route: string;
  info: string;
  maximize: boolean;
  unit: string;
  thresholds: {
    warning: number;
    danger: number;
  };
}
export interface KpiData {
  title: string;
  value: number;
  unit: string;
}
export interface KPI extends KpiData, KPIConfig {}
