<template>
  <q-btn-dropdown
    :outline="!compact"
    :flat="compact"
    :dense="compact"
    :label="currentLocaleLabel"
    :size="compact ? 'sm' : undefined"
  >
    <q-list>
      <q-item
        v-for="locale in locales"
        :key="locale.value"
        clickable
        v-close-popup
        @click="changeLocale(locale.value)"
        :active="locale.value === currentLocale"
      >
        <q-item-section>
          <q-item-label>{{ locale.label }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-list>
  </q-btn-dropdown>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { computed } from 'vue';

interface Props {
  compact?: boolean;
}

withDefaults(defineProps<Props>(), {
  compact: false,
});

const { locale, availableLocales } = useI18n();

const locales = computed(() =>
  availableLocales.map((loc) => ({
    value: loc,
    label: (loc.split('-')[0] || loc).toUpperCase(),
  })),
);

const currentLocale = computed(() => locale.value);

const currentLocaleLabel = computed(() => (locale.value.split('-')[0] || 'en').toUpperCase());

const changeLocale = (newLocale: string) => {
  locale.value = newLocale;
  // Optionally save to localStorage
  localStorage.setItem('userLocale', newLocale);
};
</script>
