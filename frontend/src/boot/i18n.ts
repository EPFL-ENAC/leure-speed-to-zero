import { boot } from 'quasar/wrappers';
import { createI18n } from 'vue-i18n';
import messages from '../i18n';

export type MessageLanguages = keyof typeof messages;
// Type-define 'en-US' as the master schema for the resource
export type MessageSchema = (typeof messages)['en-US'];

// See https://vue-i18n.intlify.dev/guide/advanced/typescript.html#global-resource-schema-type-definition
/* eslint-disable @typescript-eslint/no-empty-object-type */
declare module 'vue-i18n' {
  // define the locale messages schema
  export interface DefineLocaleMessage extends MessageSchema {}

  // define the datetime format schema
  export interface DefineDateTimeFormat {
    [key: string]: object;
  }

  // define the number format schema
  export interface DefineNumberFormat {
    [key: string]: object;
  }
}
/* eslint-enable @typescript-eslint/no-empty-object-type */
// Create i18n instance
export const i18n = createI18n({
  locale: localStorage.getItem('userLocale') || 'en-US',
  legacy: false, // Use Composition API mode
  globalInjection: true,
  messages,
});

// Some texts change by profile (see `profiles` in the language files).
// Merge the block of the active profile over the top level texts. A profile
// with no block keeps the default texts.
export function applyProfileMessages(profile: string): void {
  for (const locale of Object.keys(messages) as MessageLanguages[]) {
    const overrides = (messages[locale].profiles as Record<string, object | undefined>)[profile];
    if (overrides) i18n.global.mergeLocaleMessage(locale, overrides);
  }
}

export default boot(({ app }) => {
  // Set i18n instance on app
  app.use(i18n);
});
