import type { TranslationObject } from './translationHelpers';
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

// One file per profile, named after it: each model team edits only the file of
// its own model. A profile with no file uses default.json.
const leverFiles = import.meta.glob<Lever[]>('../config/levers/*.json', {
  eager: true,
  import: 'default',
});

function leverFile(profile: string): Lever[] {
  return (
    leverFiles[`../config/levers/${profile}.json`] ??
    leverFiles['../config/levers/default.json'] ??
    []
  );
}

// Filled by loadLeversForProfile at boot, once the profile is known. It is
// filled in place so every module that imported it sees the levers.
export const levers: Lever[] = [];

export function loadLeversForProfile(profile: string): void {
  levers.splice(0, levers.length, ...leverFile(profile));
}
