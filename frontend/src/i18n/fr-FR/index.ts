import levers from './levers';

export default {
  failed: 'Action a échoué',
  success: 'Action réussie',
  // Common UI elements
  welcome: 'Bienvenue sur Speed to Zero',
  loading: 'Chargement...',
  save: 'Enregistrer',
  cancel: 'Annuler',
  delete: 'Supprimer',
  edit: 'Modifier',
  close: 'Fermer',
  submit: 'Soumettre',
  resetDefault: 'Réinitialiser par défaut',
  // Component-specific translations
  levers: 'Leviers',
  leverDetails: 'Détails du levier',
  selectPathway: 'Sélectionner un parcours',
  featureNotReady: 'Fonctionnalité non disponible',
  runModel: 'Exécuter le modèle',
  runModelToSeeData: 'Exécutez le modèle pour voir les données {sector}',
  clickToView: 'Cliquez pour voir les données {title}',
  backToOverview: "Retour à la vue d'ensemble",
  selectKpiToViewDetails: 'Sélectionnez un KPI pour voir les graphiques et analyses détaillés',
  showMoreInformation: "Afficher plus d'informations",
  // Chart components
  loadingChartData: 'Chargement des données du graphique...',
  retry: 'Réessayer',
  noChartDataAvailable: 'Aucune donnée de graphique disponible',
  noDataAvailable: 'Aucune donnée disponible',
  // Time periods
  historical: 'Historique',
  forecast: 'Prévision',
  // KPI translations
  kpi: {
    status: {
      excellent: 'Excellent',
      warning: 'Avertissement',
      danger: 'Danger',
    },
    higherIsBetter: 'Plus haut est meilleur',
    lowerIsBetter: 'Plus bas est meilleur',
    clickToViewDetails: 'Cliquez pour voir les graphiques détaillés',
  },
  // Nested translations
  lever: levers,
};
