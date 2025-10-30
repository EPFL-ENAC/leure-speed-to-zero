import levers from './levers';

export default {
  failed: 'Action failed',
  success: 'Action was successful',
  // Common UI elements
  welcome: 'Welcome to Speed to Zero',
  loading: 'Loading...',
  save: 'Save',
  cancel: 'Cancel',
  delete: 'Delete',
  edit: 'Edit',
  close: 'Close',
  submit: 'Submit',
  resetDefault: 'Reset to Default',
  // Component-specific translations
  levers: 'Levers',
  leverDetails: 'Lever details',
  selectPathway: 'Select Pathway',
  featureNotReady: 'Feature not ready',
  runModel: 'Run Model',
  runModelToSeeData: 'Run the model to see {sector} data',
  clickToView: 'Click to view {title} data',
  backToOverview: 'Back to Overview',
  selectKpiToViewDetails: 'Select a KPI to view detailed charts and analysis',
  showMoreInformation: 'Show more information',
  // Chart components
  loadingChartData: 'Loading chart data...',
  retry: 'Retry',
  noChartDataAvailable: 'No chart data available',
  noDataAvailable: 'No data available',
  // Time periods
  historical: 'Historical',
  forecast: 'Forecast',
  // KPI translations
  kpi: {
    status: {
      excellent: 'Excellent',
      warning: 'Warning',
      danger: 'Danger',
    },
    higherIsBetter: 'Higher is better',
    lowerIsBetter: 'Lower is better',
    clickToViewDetails: 'Click to view detailed charts',
  },
  // Nested translations
  lever: levers,
};
