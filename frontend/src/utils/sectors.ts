import type { TranslationObject } from './translationHelpers';
import { sectors as sectorsJSON } from 'src/config/sectors';
export interface Sector {
  label: string | TranslationObject;
  value: string;
  icon: string;
  levers: string[];
  disabled?: boolean;
}

export const sectors: Sector[] = sectorsJSON;

export interface KPIConfig {
  name: string | TranslationObject;
  route: string;
  info: string | TranslationObject;
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
