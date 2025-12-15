import { ref, watch } from 'vue';
import { useQuasar } from 'quasar';

/**
 * Composable for navigation drawer state management
 * Shared logic between MainLayout and DashboardLayout
 */
export function useNavigationDrawer() {
  const $q = useQuasar();

  const miniMode = ref(false);
  const navigationOpen = ref($q.screen.gt.sm);

  const toggleMiniMode = () => {
    miniMode.value = !miniMode.value;
  };

  const toggleNavigation = () => {
    navigationOpen.value = !navigationOpen.value;
  };

  watch(
    () => $q.screen.lt.md,
    (mobileMode) => {
      if (mobileMode) {
        navigationOpen.value = false;
        miniMode.value = false;
      } else {
        navigationOpen.value = true;
        miniMode.value = false;
      }
    },
  );

  return {
    miniMode,
    navigationOpen,
    toggleMiniMode,
    toggleNavigation,
  };
}
