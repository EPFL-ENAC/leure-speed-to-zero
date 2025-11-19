import { onMounted, onUnmounted } from 'vue';
import { useLeverStore } from 'stores/leversStore';

/**
 * Composable to set the current sector in the lever store
 * Automatically updates when component mounts and clears on unmount
 * @param sectorName - The name of the sector to set as current
 */
export function useCurrentSector(sectorName: string) {
  const leverStore = useLeverStore();

  onMounted(() => {
    leverStore.setCurrentSector(sectorName);
  });

  onUnmounted(() => {
    // Optionally clear the sector when leaving the page
    // Comment this out if you want to keep the last sector set
    leverStore.setCurrentSector(null);
  });

  return {
    currentSector: leverStore.currentSector,
  };
}
