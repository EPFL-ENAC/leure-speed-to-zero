import { boot } from 'quasar/wrappers';
import { loadRegionConfig } from 'src/utils/region';

export default boot(async () => {
  // Load region configuration from backend at app startup
  await loadRegionConfig();
});
