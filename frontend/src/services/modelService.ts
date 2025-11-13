import axios from 'axios';

// Determine the base URL based on environment
const getBaseUrl = () => {
  // In development mode, point to the dev server
  if (process.env.NODE_ENV === 'development') {
    return '/api';
  }

  // In production, use relative path (will use the same host as the frontend)
  return '/api';
};

// Create an axios instance with base configuration
const apiClient = axios.create({
  baseURL: getBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

export const modelService = {
  /**
   * Run the model with the provided lever values
   * @param levers - String of lever values
   * @returns Promise with model results
   */
  runModel(levers: string) {
    return apiClient.get('/v1/run-model-clean-structure', {
      params: { levers },
    });
  },

  // Add other API methods as needed
  getVersion() {
    return apiClient.get('/v1/version');
  },

  getDatamatrix(name: string) {
    return apiClient.get(`/v1/datamatrix/${name}`);
  },

  /**
   * Get lever data for plotting/visualization
   * @param leverName - The name of the lever to get data for (default: "lever_heatcool-behaviour")
   * @param modules - Comma-separated list of modules (default: "transport,buildings")
   * @param country - Country to get data for (optional, uses default region if not provided)
   * @returns Promise with lever data results
   */
  getLeverData(leverName: string, modules?: string, country?: string) {
    const params: Record<string, string> = {};
    if (modules) params.modules = modules;
    if (country) params.country = country;

    return apiClient.get(`/v1/lever-data/${leverName}`, {
      params,
    });
  },
};
