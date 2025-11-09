# Internationalization (i18n) Guide

## Quick Start

### Adding translations

1. Add your translations to the language files:
   - `/src/i18n/en-US/index.ts` for English
   - `/src/i18n/fr-FR/index.ts` for French

### Using translations in components

#### In Template (Composition API)

```vue
<template>
  <div>{{ $t('welcome') }}</div>
  <q-btn :label="$t('save')" />
</template>
```

#### In Script Setup

```vue
<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const message = t('welcome');
</script>
```

### Language Switcher

Use the `LanguageSwitcher` component in your layout:

```vue
<template>
  <q-layout>
    <q-header>
      <q-toolbar>
        <q-toolbar-title>My App</q-toolbar-title>
        <LanguageSwitcher />
      </q-toolbar>
    </q-header>
  </q-layout>
</template>

<script setup lang="ts">
import LanguageSwitcher from 'components/LanguageSwitcher.vue';
</script>
```

## Adding More Languages

1. Create a new folder in `/src/i18n/` (e.g., `de-DE` for German)
2. Add an `index.ts` file with translations
3. Import and add it to `/src/i18n/index.ts`
4. Add the locale to the `LanguageSwitcher.vue` component

## Advanced Features

### Pluralization

```typescript
// In language file
export default {
  car: 'car | cars',
  apple: 'no apples | one apple | {count} apples',
};

// In component
{
  {
    $t('car', 2);
  }
} // outputs: cars
{
  {
    $t('apple', 0);
  }
} // outputs: no apples
{
  {
    $t('apple', 1);
  }
} // outputs: one apple
{
  {
    $t('apple', { count: 10 });
  }
} // outputs: 10 apples
```

### Variables

```typescript
// In language file
export default {
  greeting: 'Hello, {name}!',
};

// In component
{
  {
    $t('greeting', { name: 'John' });
  }
} // outputs: Hello, John!
```

## TypeScript Support

The setup includes full TypeScript support. The English (`en-US`) translations serve as the master schema, ensuring all other languages have the same keys.
