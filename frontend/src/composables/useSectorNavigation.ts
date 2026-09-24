import { computed } from 'vue';
import { sectors } from 'utils/sectors';
import { getProfileSectors, getLeverKeys } from 'src/utils/region';
import type { TranslationObject } from 'src/utils/translationHelpers';

type SubtabConfig = Array<{ route: string; title: TranslationObject }>;

// Dynamically import all subtab configs
const subtabModules = import.meta.glob<{ subtabs?: SubtabConfig }>('../config/subtabs/*.json', {
  eager: true,
});

// Build subtabs map keyed by sector value
const subtabsMapData: Record<string, SubtabConfig> = {};
for (const sector of sectors) {
  const configPath = `../config/subtabs/${sector.value}.json`;
  const module = subtabModules[configPath];

  if (!module) {
    console.warn(
      `⚠️ Missing subtabs configuration for sector "${sector.value}".\n` +
        `Expected file: src/config/subtabs/${sector.value}.json\n` +
        `This sector will have no subtabs in navigation.`,
    );
  } else if (!module.subtabs || module.subtabs.length === 0) {
    console.warn(
      `⚠️ Empty or missing "subtabs" array in configuration for sector "${sector.value}".\n` +
        `File: src/config/subtabs/${sector.value}.json\n` +
        `This sector will have no subtabs in navigation.`,
    );
  }

  subtabsMapData[sector.value] = module?.subtabs || [];
}

export function useSectorNavigation() {
  const subtabsMap = computed(() => subtabsMapData);

  const getNavigationTarget = (sectorName: string) => {
    const subtabs = subtabsMap.value[sectorName];
    if (subtabs && subtabs.length > 0 && subtabs[0]) {
      return { name: sectorName, params: { subtab: subtabs[0].route } };
    }
    return { name: sectorName };
  };

  // Sectors this deployment shows, in the order the profile lists them.
  // No profile (empty list) means every sector, as before.
  const availableSectors = computed(() => {
    const wanted = getProfileSectors();
    if (wanted.length === 0) return sectors;
    return wanted
      .map((value) => sectors.find((s) => s.value === value))
      .filter((s): s is (typeof sectors)[number] => s !== undefined)
      .map((s) => ({ ...s, disabled: false }));
  });

  // Levers the loaded model knows about. A sector may list a lever a given
  // model does not have, hide it instead of sending a dead slider.
  const leversFor = (sectorValue: string): string[] => {
    const sector = sectors.find((s) => s.value === sectorValue);
    if (!sector) return [];
    const known = getLeverKeys();
    if (known.length === 0) return sector.levers;
    return sector.levers.filter((code) => known.includes(code));
  };

  // Overall sector (kept for backward compatibility)
  const overallSector = computed(() => sectors.find((s) => s.value === 'overall'));

  return {
    sectors,
    subtabsMap,
    availableSectors,
    leversFor,
    overallSector,
    getNavigationTarget,
  };
}
