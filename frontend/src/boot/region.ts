import { boot } from 'quasar/wrappers';
import { getProfile, loadRegionConfig } from 'src/utils/region';
import { loadLeversForProfile } from 'src/utils/leversData';

export default boot(async () => {
  // Load region configuration from backend at app startup
  await loadRegionConfig();
  // The lever texts depend on the profile, so they come after the config
  loadLeversForProfile(getProfile());
});
