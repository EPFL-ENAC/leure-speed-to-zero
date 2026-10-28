import { ref } from 'vue';
import { modelService } from 'src/services/modelService';

// One calibration_rates call of the model: rate = reference / raw, per category
export interface Calibration {
  id: string;
  module: string;
  function: string;
  variable: string;
  calibration_window: [number, number];
  scope: string;
  years: number[];
  series: Array<{ name: string; values: Array<number | null> }>;
}

interface CalibrationResponse {
  status: string;
  message?: string;
  country: string;
  modules: Array<{ module: string; calibrations: Calibration[] }>;
}

// The rates do not depend on the levers, so they are fetched once per session
const modules = ref<Record<string, Calibration[]> | null>(null);
const isLoading = ref(false);
const error = ref<string | null>(null);

async function load(): Promise<void> {
  if (modules.value || isLoading.value) return;
  isLoading.value = true;
  error.value = null;
  try {
    const { data } = await modelService.getCalibrationRates();
    const response = data as CalibrationResponse;
    if (response.status !== 'success') throw new Error(response.message ?? response.status);
    modules.value = Object.fromEntries(response.modules.map((m) => [m.module, m.calibrations]));
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    isLoading.value = false;
  }
}

export function useCalibrationRates() {
  return { modules, isLoading, error, load };
}
