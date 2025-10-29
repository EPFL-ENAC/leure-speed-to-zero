/**
 * Type for translation objects in JSON configs
 */
export interface TranslationObject {
  enUS: string;
  frFR: string;
  deDE: string;
}

/**
 * Type guard to check if a value is a TranslationObject
 */
export function isTranslationObject(value: unknown): value is TranslationObject {
  return (
    typeof value === 'object' &&
    value !== null &&
    'enUS' in value &&
    'frFR' in value &&
    'deDE' in value
  );
}

/**
 * Get translated text from either a string or a TranslationObject
 * @param value - Either a string or a TranslationObject
 * @param locale - Current locale string (e.g., 'en-US')
 * @param fallback - Optional fallback text if translation not found
 * @returns Translated text
 */
export function getTranslatedText(
  value: string | TranslationObject,
  locale: string,
  fallback = '',
): string {
  // If it's already a string, return it
  if (typeof value === 'string') {
    return value;
  }

  // If it's a translation object, get the correct locale
  if (isTranslationObject(value)) {
    // Map locale format (e.g., 'en-US' to 'enUS')
    const localeKey = locale.replace('-', '') as keyof TranslationObject;

    // Return the translation for the current locale, fallback to enUS, then to fallback
    return value[localeKey] || value.enUS || fallback;
  }

  return fallback;
}
