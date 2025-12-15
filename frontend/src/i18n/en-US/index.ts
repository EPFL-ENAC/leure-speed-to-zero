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
  // Navigation
  home: 'Home',
  about: 'About',
  legal: 'Legal',
  launchApp: 'Launch Calculator',
  openCalculator: 'Open Calculator',
  tryCalculator: 'Try Calculator',
  allRightsReserved: 'All rights reserved',
  learnMore: 'Learn More',
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
  keyMetrics: 'Key Metrics',
  // Chart components
  loadingChartData: 'Loading chart data...',
  retry: 'Retry',
  noChartDataAvailable: 'No chart data available',
  noDataAvailable: 'No data available',
  downloadCSV: 'Download CSV',
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
  // Home Page
  welcomeToSpeedToZero: 'Welcome to Speed to Zero',
  homeSubtitle: 'Interactive carbon neutrality calculator for Switzerland',
  exploreBySector: 'Explore by Sector',
  selectSector: 'Select a Sector',
  selectSectorDesc: 'Choose from buildings, transport, agriculture, or forestry',
  adjustLevers: 'Adjust Policy Levers',
  adjustLeversDesc: 'Configure interventions and see their impact in real-time',
  analyzeResults: 'Analyze Results',
  analyzeResultsDesc: 'Visualize emissions, energy consumption, and key performance indicators',
  // About Page
  aboutTitle: 'About Speed to Zero',
  ourMission: 'Our Mission',
  ourMissionDesc:
    'Speed to Zero is a comprehensive carbon neutrality modeling tool designed to help policymakers, researchers, and organizations explore pathways to achieve net-zero emissions. Our mission is to provide transparent, data-driven insights into the complex transitions required across multiple sectors of the economy.',
  whatWeOffer: 'What We Offer',
  whatWeOfferDesc: 'Our platform provides detailed modeling and analysis across key sectors:',
  buildingsSector: 'Buildings Sector',
  buildingsSectorDesc:
    'Model heating, cooling, and energy efficiency improvements in residential and commercial buildings',
  transportSector: 'Transport Sector',
  transportSectorDesc:
    'Analyze transitions to electric vehicles, public transport, and sustainable mobility',
  agricultureSector: 'Agriculture Sector',
  agricultureSectorDesc: 'Explore sustainable farming practices and emission reduction strategies',
  forestrySector: 'Forestry Sector',
  forestrySectorDesc: 'Understand carbon sequestration potential and sustainable forest management',
  howItWorks: 'How It Works',
  howItWorksDesc:
    'Speed to Zero uses a sophisticated modeling engine that allows you to adjust policy levers and immediately see the impact on emissions, energy consumption, and other key metrics. The calculator combines historical data with forward-looking scenarios to provide comprehensive insights into potential pathways to carbon neutrality.',
  theTeam: 'The Team',
  theTeamDesc:
    'Speed to Zero is developed and maintained by EPFL (École polytechnique fédérale de Lausanne), bringing together expertise in climate science, energy systems, and data visualization.',
  startExploring: 'Start Exploring',
  // Legal Page
  legalNotice: 'Legal Notice',
  termsOfUse: 'Terms of Use',
  termsOfUseDesc:
    'By accessing and using Speed to Zero, you agree to these terms of use. This calculator is provided for informational and research purposes. While we strive for accuracy, the projections and models should not be used as the sole basis for policy or investment decisions.',
  privacyPolicy: 'Privacy Policy',
  privacyPolicyDesc:
    'We respect your privacy. Speed to Zero does not collect personal information unless you explicitly provide it. Any data you input into the calculator remains on your device and is not transmitted to our servers without your consent.',
  dataUsage: 'Data Usage',
  dataUsageDesc:
    'The underlying data used in our models comes from publicly available sources including Eurostat, national statistics agencies, and research institutions. All data sources are documented and referenced within the application.',
  disclaimer: 'Disclaimer',
  disclaimerDesc:
    'The models and projections provided by Speed to Zero are based on assumptions and historical data. Actual outcomes may vary significantly. EPFL and the project contributors are not liable for decisions made based on the information provided by this calculator.',
  intellectualProperty: 'Intellectual Property',
  intellectualPropertyDesc:
    'Speed to Zero is open source software. The code and methodology are available for review and contribution. Please see our GitHub repository for licensing details.',
  contact: 'Contact',
  contactDesc:
    'For questions, feedback, or collaboration opportunities, please contact us through the EPFL ENAC faculty website.',
  lastUpdated: 'Last updated',
  // Welcome Popup
  welcomePopup: {
    subtitle: 'Interactive carbon neutrality calculator for Switzerland',
    description:
      'Explore pathways to net-zero emissions by adjusting policy levers and visualizing their impact across different sectors.',
    featureLevers: 'Adjust policy levers to model interventions',
    featureVisualize: 'Visualize emissions and energy metrics',
    featureCompare: 'Compare scenarios across sectors',
    dontShowAgain: "Don't show this again",
    startTutorial: 'Start Tutorial',
    skipTutorial: 'Skip',
  },
  // Tour translations
  tour: {
    sectors:
      'Welcome! Start by selecting a sector from this menu. Each sector has detailed sub-tabs with charts and analysis.',
    levers:
      'These are policy levers. Adjust them to see how different interventions impact the results. Click to expand and see detailed options.',
    kpis: 'Key Performance Indicators show the main metrics for the selected sector. They update in real-time as you adjust levers.',
    charts:
      'Detailed charts and visualizations appear here. They provide in-depth analysis of emissions, energy consumption, and other metrics.',
    skip: 'Skip',
    next: 'Next',
    back: 'Back',
    finish: 'Got it!',
  },
  // Nested translations
  lever: levers,
};
