import { type TranslationObject } from 'src/utils/translationHelpers';
import labels from 'src/config/plotLabels.json';
// /**
//  * Get a translated plot label if available, otherwise return the key
//  * @param key - The label key to translate (may include unit like "variable[TWh]")
//  * @param i18n - The i18n instance from useI18n() (optional for backwards compatibility)
//  * @returns The translated label or the original key
//  */
// export function getPlotLabel(key: string, i18n?: { t: Composer['t']; te: Composer['te'] }): string {
//   if (i18n) {
//     const translationKey = `plotLabels['${key}']`;
//     // Check if translation exists first
//     if (i18n.te(translationKey)) {
//       return i18n.t(translationKey);
//     }
//   }
//   return key;
// }

export const plotLabels: Record<string, TranslationObject | string> = labels;
