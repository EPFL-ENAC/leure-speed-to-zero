import type { TranslationObject } from './translationHelpers';
import { levers as leversData } from 'src/config/levers';
export interface DifficultyArea {
  min: number;
  max: number;
  color: string;
  label: string;
}

export interface Lever {
  code: string;
  title: string | TranslationObject;
  group: string | TranslationObject;
  headline: string | TranslationObject;
  popupText?: string | TranslationObject;
  disabled?: boolean;
  range: (string | number)[];
  type: string;
  difficultyColors: DifficultyArea[];
}

export const levers: Lever[] = leversData;
