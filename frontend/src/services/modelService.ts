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
   * @param sector - Optional sector to run (will run only necessary dependencies)
   * @returns Promise with model results
   */
  runModel(levers: string, sector?: string) {
    return apiClient.get('/v1/run-model-clean-structure', {
      params: { levers, sector },
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
   * @param sector - Sector to get data for (optional, uses all sectors if not provided)
   * @param country - Country to get data for (optional, uses default region if not provided)
   * @returns Promise with lever data results
   */
  getLeverData(leverName: string, sector?: string, country?: string) {
    const params: Record<string, string> = {};
    if (sector) params.sector = sector;
    if (country) params.country = country;

    return apiClient.get(`/v1/lever-data/${leverName}`, {
      params,
    });
  },
};
