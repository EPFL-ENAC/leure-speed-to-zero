<template>
  <aside class="vertical-nav">
    <!-- Logo/Header -->
    <div class="nav-header">
      <div class="nav-logo">
        <!-- Use SVG logo from public folder -->
        <img src="/speed2zero-logo-final.svg" alt="Speed to Zero" class="logo-svg" />
      </div>
    </div>

    <!-- Main Navigation -->
    <nav class="nav-content">
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

      <!-- Sectors Section -->
      <div class="nav-section">
        <!-- Overall -->
        <div
          v-if="overallSector"
          class="nav-item-expandable"
          :class="{ active: isActive('overall'), disabled: overallSector.disabled }"
        >
          <div class="nav-item" @click="toggleSection('overall')">
            <q-icon :name="overallSector.icon" class="nav-item-icon" />
            <span v-if="!mini" class="nav-item-label">{{ getLabel(overallSector.label) }}</span>
            <q-icon
              v-if="!mini && overallSubtabs.length > 0"
              name="expand_more"
              class="expand-icon"
              :class="{ expanded: expandedSections.has('overall') }"
            />
          </div>
          <div v-if="!mini && expandedSections.has('overall')" class="sub-nav">
            <router-link
              v-for="subtab in overallSubtabs"
              :key="subtab.route"
              :to="{ name: 'overall', params: { subtab: subtab.route } }"
              class="sub-nav-item"
              :class="{ active: isSubtabActive('overall', subtab.route) }"
            >
              {{ getLabel(subtab.title) }}
            </router-link>
          </div>
        </div>

        <!-- Other Sectors -->
        <div
          v-for="sector in activeSectors"
          :key="sector.value"
          class="nav-item-expandable"
          :class="{ active: isActive(sector.value), disabled: sector.disabled }"
        >
          <div class="nav-item" @click="toggleSection(sector.value)">
            <q-icon :name="sector.icon" class="nav-item-icon" />
            <span v-if="!mini" class="nav-item-label">{{ getLabel(sector.label) }}</span>
            <q-icon
              v-if="!mini && (subtabsMap[sector.value]?.length ?? 0) > 0"
              name="expand_more"
              class="expand-icon"
              :class="{ expanded: expandedSections.has(sector.value) }"
            />
          </div>
          <div v-if="!mini && expandedSections.has(sector.value)" class="sub-nav">
            <router-link
              v-for="subtab in subtabsMap[sector.value]"
              :key="subtab.route"
              :to="{ name: sector.value, params: { subtab: subtab.route } }"
              class="sub-nav-item"
              :class="{ active: isSubtabActive(sector.value, subtab.route) }"
            >
              {{ getLabel(subtab.title) }}
            </router-link>
          </div>
        </div>
      </div>
    </nav>

    <!-- Footer Section -->
    <div v-if="!mini" class="nav-footer">
      <region-flag />
      <language-switcher />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { sectors } from 'utils/sectors';
import { getTranslatedText, type TranslationObject } from 'src/utils/translationHelpers';
import LanguageSwitcher from './LanguageSwitcher.vue';
import RegionFlag from './RegionFlag.vue';

// Import subtab configs
import buildingsConfig from 'config/subtabs/buildings.json';
import transportConfig from 'config/subtabs/transport.json';
import forestryConfig from 'config/subtabs/forestry.json';
import agricultureConfig from 'config/subtabs/agriculture.json';
import overallConfig from 'config/subtabs/overall.json';

interface Props {
  mini?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  mini: false,
});

const route = useRoute();
const { locale } = useI18n();

// Main pages configuration
const mainPages = [
  { name: 'home', label: { enUS: 'Home', frFR: 'Accueil', deDE: 'Startseite' }, icon: 'home' },
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

// Subtabs configuration map
const subtabsMap = computed<Record<string, Array<{ route: string; title: TranslationObject }>>>(
  () => ({
    buildings: buildingsConfig.subtabs || [],
    transport: transportConfig.subtabs || [],
    forestry: forestryConfig.subtabs || [],
    agriculture: agricultureConfig.subtabs || [],
    overall: overallConfig.subtabs || [],
  }),
);

// Separate Overall sector from others
const overallSector = computed(() => sectors.find((s) => s.value === 'overall'));
const overallSubtabs = computed(() => subtabsMap.value.overall || []);

const activeSectors = computed(() => sectors.filter((s) => s.value !== 'overall'));

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

// Toggle section expand/collapse
const toggleSection = (sectionName: string) => {
  if (props.mini) return;

  const sector = sectors.find((s) => s.value === sectionName);
  if (sector?.disabled) return;

  // If no subtabs, just navigate
  const subtabs = subtabsMap.value[sectionName];
  if (!subtabs?.length && sectionName !== 'overall') {
    return;
  }

  if (expandedSections.value.has(sectionName)) {
    expandedSections.value.delete(sectionName);
  } else {
    expandedSections.value.add(sectionName);
  }
  saveExpandedState();
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
.vertical-nav {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.nav-header {
  flex-shrink: 0;
  padding: 24px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: -0.02em;
}

.logo-icon {
  color: var(--q-primary);
}

.logo-text {
  white-space: nowrap;
}

.logo-svg {
  width: 100%;
  border-radius: 0.2rem;
  display: block;
  object-fit: contain;
}

.nav-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 16px 0;
  scrollbar-gutter: stable;

  /* Custom scrollbar */
  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.1);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 0, 0, 0.15);
  }
}

.nav-section {
  padding: 8px 0;

  & + & {
    border-top: 1px solid rgba(0, 0, 0, 0.06);
    margin-top: 8px;
    padding-top: 16px;
  }
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  color: #6e6e73;
  text-decoration: none;
  cursor: pointer;
  transition: all 150ms ease;
  font-size: small;
  font-weight: 400;
  user-select: none;

  &:hover {
    background: #f5f5f7;
    color: #1a1a1a;

    .nav-item-icon {
      opacity: 1;
    }
  }

  &.active {
    color: #1a1a1a;
    font-weight: 500;

    .nav-item-icon {
      opacity: 1;
    }
  }
}

.nav-item-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  font-size: 20px;
  margin-right: 12px;
  opacity: 0.7;
  transition: opacity 150ms ease;
}

.nav-item-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-item-expandable {
  &.disabled {
    .nav-item {
      opacity: 0.4;
      cursor: not-allowed;
      pointer-events: none;
    }
  }

  &.active > .nav-item {
    color: #1a1a1a;
    font-weight: 500;

    .nav-item-icon {
      opacity: 1;
    }
  }
}

.expand-icon {
  flex-shrink: 0;
  font-size: 16px;
  margin-left: auto;
  opacity: 0.5;
  transition: transform 200ms ease;

  &.expanded {
    transform: rotate(180deg);
  }
}

.sub-nav {
  animation: expandDown 200ms ease;
  overflow: hidden;
}

@keyframes expandDown {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.sub-nav-item {
  display: block;
  padding: 8px 20px 8px 52px;
  color: #999;
  text-decoration: none;
  font-size: 13px;
  line-height: 1.4;
  cursor: pointer;
  transition: color 150ms ease;
  letter-spacing: -0.01em;
  word-wrap: break-word;
  overflow-wrap: break-word;

  &:hover {
    color: #1a1a1a;
  }

  &.active {
    color: #1a1a1a;
    font-weight: 500;
  }
}

.nav-footer {
  flex-shrink: 0;
  padding: 16px 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Mini mode adjustments */
.vertical-nav.mini {
  .nav-logo {
    justify-content: center;
  }

  .nav-item {
    justify-content: center;
    padding: 10px;
  }

  .nav-item-icon {
    margin-right: 0;
  }
  .logo-svg {
    height: 24px;
  }
}

/* Mobile responsiveness */
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
