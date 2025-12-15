<template>
  <aside class="vertical-nav" :class="{ mini }">
    <div class="nav-header">
      <img src="/speed2zero-logo-final.svg" alt="Speed to Zero" class="logo-svg" />
    </div>

    <nav class="nav-content">
      <!-- Sectors Section -->
      <div class="nav-section">
        <!-- Overall -->
        <router-link
          v-if="overallSector"
          :to="getNavigationTarget('overall')"
          class="nav-item"
          :class="{ active: isActive('overall'), disabled: overallSector.disabled }"
          @click="(e) => handleSectorClick(e, 'overall')"
        >
          <q-icon :name="overallSector.icon" class="nav-item-icon" />
          <span v-if="!mini" class="nav-item-label">{{ getLabel(overallSector.label) }}</span>
          <q-icon
            v-if="!mini && overallSubtabs.length > 0"
            name="expand_more"
            class="expand-icon"
            :class="{ expanded: expandedSections.has('overall') }"
            @click.prevent="toggleExpand('overall')"
          />
        </router-link>
        <template v-if="!mini && expandedSections.has('overall')">
          <router-link
            v-for="subtab in overallSubtabs"
            :key="subtab.route"
            :to="{ name: 'overall', params: { subtab: subtab.route } }"
            class="sub-nav-item"
            :class="{ active: isSubtabActive('overall', subtab.route) }"
          >
            {{ getLabel(subtab.title) }}
          </router-link>
        </template>

        <!-- Other Sectors -->
        <template v-for="sector in activeSectors" :key="sector.value">
          <router-link
            :to="getNavigationTarget(sector.value)"
            class="nav-item"
            :class="{ active: isActive(sector.value), disabled: sector.disabled }"
            @click="(e) => handleSectorClick(e, sector.value)"
          >
            <q-icon :name="sector.icon" class="nav-item-icon" />
            <span v-if="!mini" class="nav-item-label">{{ getLabel(sector.label) }}</span>
            <q-icon
              v-if="!mini && (subtabsMap[sector.value]?.length ?? 0) > 0 && !sector.disabled"
              name="expand_more"
              class="expand-icon"
              :class="{ expanded: expandedSections.has(sector.value) }"
              @click.prevent="toggleExpand(sector.value)"
            />
          </router-link>
          <template v-if="!mini && expandedSections.has(sector.value) && !sector.disabled">
            <router-link
              v-for="subtab in subtabsMap[sector.value]"
              :key="subtab.route"
              :to="{ name: sector.value, params: { subtab: subtab.route } }"
              class="sub-nav-item"
              :class="{ active: isSubtabActive(sector.value, subtab.route) }"
            >
              {{ getLabel(subtab.title) }}
            </router-link>
          </template>
        </template>
      </div>
    </nav>
    <!-- Main Pages Section -->
    <div class="nav-section">
      <router-link
        v-for="page in mainPages"
        :key="page.name"
        :to="{ name: page.name }"
        class="nav-item"
        :class="{ active: isActive(page.name) }"
      >
        <q-icon :name="page.icon" class="nav-item-icon" />
        <span v-if="!mini" class="nav-item-label">{{ getLabel(page.label) }}</span>
      </router-link>
    </div>

    <!-- Footer Section -->
    <div v-if="!mini" class="nav-footer">
      <region-flag />
      <language-switcher />
    </div>

    <!-- Collapse Toggle Button -->
    <div class="nav-toggle">
      <q-btn
        flat
        dense
        round
        :icon="mini ? 'chevron_right' : 'chevron_left'"
        size="sm"
        class="toggle-btn"
        @click="emit('toggle')"
      />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { getTranslatedText, type TranslationObject } from 'src/utils/translationHelpers';
import { useSectorNavigation } from 'src/composables/useSectorNavigation';
import LanguageSwitcher from './LanguageSwitcher.vue';
import RegionFlag from './RegionFlag.vue';

const emit = defineEmits<{
  toggle: [];
}>();

const {
  subtabsMap,
  availableSectors: activeSectors,
  overallSector,
  getNavigationTarget,
} = useSectorNavigation();

interface Props {
  mini?: boolean;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const props = withDefaults(defineProps<Props>(), {
  mini: false,
});

const route = useRoute();
const { locale } = useI18n();

// Main pages configuration
const mainPages = [
  { name: 'about', label: { enUS: 'About', frFR: 'À propos', deDE: 'Über' }, icon: 'info' },
  {
    name: 'legal',
    label: { enUS: 'Legal', frFR: 'Mentions légales', deDE: 'Impressum' },
    icon: 'gavel',
  },
];

// Expanded sections state (persisted to localStorage)
const expandedSections = ref<Set<string>>(new Set());

// Load expanded state from localStorage
const loadExpandedState = () => {
  try {
    const saved = localStorage.getItem('nav-expanded-sections');
    if (saved) {
      expandedSections.value = new Set(JSON.parse(saved));
    }
  } catch (e) {
    console.error('Failed to load navigation state:', e);
  }
};

// Save expanded state to localStorage
const saveExpandedState = () => {
  try {
    localStorage.setItem('nav-expanded-sections', JSON.stringify([...expandedSections.value]));
  } catch (e) {
    console.error('Failed to save navigation state:', e);
  }
};

loadExpandedState();

// Overall subtabs
const overallSubtabs = computed(() => subtabsMap.value.overall || []);

// Helper function to get translated label
const getLabel = (label: string | TranslationObject) => {
  return getTranslatedText(label, locale.value);
};

// Check if a route is active
const isActive = (routeName: string) => {
  return route.name === routeName || route.path.split('/')[1] === routeName;
};

// Check if a subtab is active
const isSubtabActive = (sectorName: string, subtabRoute: string) => {
  return route.name === sectorName && route.params.subtab === subtabRoute;
};

// Toggle expand/collapse for subtabs
const toggleExpand = (sectionName: string) => {
  if (expandedSections.value.has(sectionName)) {
    expandedSections.value.delete(sectionName);
  } else {
    expandedSections.value.add(sectionName);
  }
  saveExpandedState();
};

// Handle sector click - toggle expansion
const handleSectorClick = (event: Event, sectorName: string) => {
  const currentSector = route.path.split('/')[1];
  // If we're already on this sector, toggle the expansion
  if (currentSector === sectorName) {
    event.preventDefault();
    toggleExpand(sectorName);
  }
};

// Auto-expand current section
watch(
  () => route.path,
  (newPath) => {
    const sector = newPath.split('/')[1];
    if (sector && (subtabsMap.value[sector]?.length ?? 0) > 0) {
      expandedSections.value.add(sector);
      saveExpandedState();
    }
  },
  { immediate: true },
);
</script>

<style lang="scss" scoped>
$border: 1px solid rgba(0, 0, 0, 0.06);
$text-muted: #6e6e73;
$text-dark: #1a1a1a;
$hover-bg: #f5f5f7;

.vertical-nav {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #fff;
  border-right: $border;
  overflow: hidden;
  position: relative;
}

.nav-header {
  padding: 1rem;
}

.logo-svg {
  width: 100%;
  border-radius: 0.2rem;
}

.nav-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-gutter: stable;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 3px;
  }
}

.nav-section {
  padding: 8px 0;
  border-top: $border;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  color: $text-muted;
  text-decoration: none;
  font-size: small;
  transition: all 150ms;

  &:hover,
  &.active {
    background: $hover-bg;
    color: $text-dark;
    .nav-item-icon {
      opacity: 1;
    }
  }
  &.active {
    font-weight: 500;
  }
  &.disabled {
    opacity: 0.4;
    pointer-events: none;
  }
}

.nav-item-icon {
  width: 20px;
  height: 20px;
  font-size: 20px;
  margin-right: 12px;
  opacity: 0.7;
}

.nav-item-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expand-icon {
  font-size: 16px;
  margin-left: auto;
  opacity: 0.5;
  transition: transform 200ms;

  &.expanded {
    transform: rotate(180deg);
  }
}

.sub-nav-item {
  display: block;
  padding: 8px 20px 8px 52px;
  color: #999;
  text-decoration: none;
  font-size: 13px;
  line-height: 1.4;

  &:hover,
  &.active {
    color: $text-dark;
  }
  &.active {
    font-weight: 500;
  }
}

.nav-footer {
  padding: 16px 20px;
  border-top: $border;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.nav-toggle {
  position: fixed;
  top: 50%;
  right: -12px;
  transform: translateY(-50%);
  z-index: 10;
}

.toggle-btn {
  background: #fff;
  border: $border;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  color: $text-muted;

  &:hover {
    background: $hover-bg;
    color: $text-dark;
  }
}

.vertical-nav.mini {
  .nav-header {
    padding: 24px 10px;
    visibility: hidden;
  }
  .logo-svg {
    height: 24px;
    width: auto;
  }
  .nav-item {
    justify-content: center;
    padding: 10px;
  }
  .nav-item-icon {
    margin-right: 0;
  }

  .nav-content {
    scrollbar-gutter: initial;
  }
}

@media (max-width: 600px) {
  .nav-header {
    padding: 16px;
  }
  .nav-item {
    padding: 12px 16px;
  }
  .sub-nav-item {
    padding: 10px 16px 10px 48px;
  }
}
</style>
