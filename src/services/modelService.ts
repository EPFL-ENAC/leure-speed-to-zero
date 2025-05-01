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
    return apiClient.get('/v1/run-model', {
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
};
