import { computed } from 'vue';
import { sectors } from 'utils/sectors';
import type { TranslationObject } from 'src/utils/translationHelpers';

// Dynamically import all subtab configs
const subtabModules = import.meta.glob<{
  subtabs?: Array<{ route: string; title: TranslationObject }>;
}>('../config/subtabs/*.json', { eager: true });

// Build subtabs map from dynamic imports
function buildSubtabsMap(): Record<string, Array<{ route: string; title: TranslationObject }>> {
  const map: Record<string, Array<{ route: string; title: TranslationObject }>> = {};

  for (const [path, module] of Object.entries(subtabModules)) {
    // Extract sector name from path: '../config/subtabs/buildings.json' -> 'buildings'
    const match = path.match(/\/([^/]+)\.json$/);
    if (match?.[1]) {
      map[match[1]] = module.subtabs || [];
    }
  }

  return map;
}

const subtabsMapData = buildSubtabsMap();

export function useSectorNavigation() {
  const subtabsMap = computed(() => subtabsMapData);

  const getNavigationTarget = (sectorName: string) => {
    const subtabs = subtabsMap.value[sectorName];
    if (subtabs && subtabs.length > 0 && subtabs[0]) {
      return { name: sectorName, params: { subtab: subtabs[0].route } };
    }
    return { name: sectorName };
  };

  // Sectors without 'overall'
  const availableSectors = computed(() => sectors.filter((s) => s.value !== 'overall'));

  // Overall sector
  const overallSector = computed(() => sectors.find((s) => s.value === 'overall'));

  return {
    sectors,
    subtabsMap,
    availableSectors,
    overallSector,
    getNavigationTarget,
  };
}
