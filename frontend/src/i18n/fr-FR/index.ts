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
  // Navigation
  home: 'Accueil',
  about: 'À propos',
  legal: 'Mentions légales',
  launchApp: 'Ouvrir le calculateur',
  openCalculator: 'Ouvrir le calculateur',
  tryCalculator: 'Essayer le calculateur',
  allRightsReserved: 'Tous droits réservés',
  learnMore: 'En savoir plus',
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
  keyMetrics: 'Indicateurs clés',
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
  // Home Page
  welcomeToSpeedToZero: 'Bienvenue sur Speed to Zero',
  homeSubtitle: 'Calculateur interactif de neutralité carbone pour la Suisse',
  exploreBySector: 'Explorer par secteur',
  selectSector: 'Sélectionner un secteur',
  selectSectorDesc: "Choisissez parmi le bâtiment, les transports, l'agriculture ou la foresterie",
  adjustLevers: 'Ajuster les leviers politiques',
  adjustLeversDesc: 'Configurez les interventions et voyez leur impact en temps réel',
  analyzeResults: 'Analyser les résultats',
  analyzeResultsDesc:
    "Visualisez les émissions, la consommation d'énergie et les indicateurs de performance",
  // About Page
  aboutTitle: 'À propos de Speed to Zero',
  ourMission: 'Notre mission',
  ourMissionDesc:
    "Speed to Zero est un outil complet de modélisation de la neutralité carbone conçu pour aider les décideurs, chercheurs et organisations à explorer les parcours pour atteindre les émissions nettes zéro. Notre mission est de fournir des informations transparentes et basées sur les données concernant les transitions complexes requises dans plusieurs secteurs de l'économie.",
  whatWeOffer: 'Ce que nous offrons',
  whatWeOfferDesc:
    'Notre plateforme fournit une modélisation et une analyse détaillées dans les secteurs clés :',
  buildingsSector: 'Secteur du bâtiment',
  buildingsSectorDesc:
    "Modélisez le chauffage, la climatisation et les améliorations de l'efficacité énergétique dans les bâtiments résidentiels et commerciaux",
  transportSector: 'Secteur des transports',
  transportSectorDesc:
    'Analysez les transitions vers les véhicules électriques, les transports publics et la mobilité durable',
  agricultureSector: 'Secteur agricole',
  agricultureSectorDesc:
    'Explorez les pratiques agricoles durables et les stratégies de réduction des émissions',
  forestrySector: 'Secteur forestier',
  forestrySectorDesc:
    'Comprenez le potentiel de séquestration du carbone et la gestion durable des forêts',
  howItWorks: 'Comment ça marche',
  howItWorksDesc:
    "Speed to Zero utilise un moteur de modélisation sophistiqué qui vous permet d'ajuster les leviers politiques et de voir immédiatement l'impact sur les émissions, la consommation d'énergie et d'autres indicateurs clés. Le calculateur combine des données historiques avec des scénarios prospectifs pour fournir des informations complètes sur les parcours potentiels vers la neutralité carbone.",
  theTeam: "L'équipe",
  theTeamDesc:
    "Speed to Zero est développé et maintenu par l'EPFL (École polytechnique fédérale de Lausanne), réunissant une expertise en science du climat, systèmes énergétiques et visualisation de données.",
  startExploring: "Commencer l'exploration",
  // Legal Page
  legalNotice: 'Mentions légales',
  termsOfUse: "Conditions d'utilisation",
  termsOfUseDesc:
    "En accédant et en utilisant Speed to Zero, vous acceptez ces conditions d'utilisation. Ce calculateur est fourni à des fins d'information et de recherche. Bien que nous nous efforcions d'être précis, les projections et modèles ne doivent pas être utilisés comme seule base pour des décisions politiques ou d'investissement.",
  privacyPolicy: 'Politique de confidentialité',
  privacyPolicyDesc:
    "Nous respectons votre vie privée. Speed to Zero ne collecte pas d'informations personnelles à moins que vous ne les fournissiez explicitement. Toutes les données que vous saisissez dans le calculateur restent sur votre appareil et ne sont pas transmises à nos serveurs sans votre consentement.",
  dataUsage: 'Utilisation des données',
  dataUsageDesc:
    "Les données sous-jacentes utilisées dans nos modèles proviennent de sources publiquement disponibles, notamment Eurostat, les agences nationales de statistiques et les institutions de recherche. Toutes les sources de données sont documentées et référencées dans l'application.",
  disclaimer: 'Clause de non-responsabilité',
  disclaimerDesc:
    "Les modèles et projections fournis par Speed to Zero sont basés sur des hypothèses et des données historiques. Les résultats réels peuvent varier considérablement. L'EPFL et les contributeurs du projet ne sont pas responsables des décisions prises sur la base des informations fournies par ce calculateur.",
  intellectualProperty: 'Propriété intellectuelle',
  intellectualPropertyDesc:
    'Speed to Zero est un logiciel open source. Le code et la méthodologie sont disponibles pour examen et contribution. Veuillez consulter notre dépôt GitHub pour les détails de licence.',
  contact: 'Contact',
  contactDesc:
    "Pour toute question, retour d'information ou opportunité de collaboration, veuillez nous contacter via le site web de la faculté ENAC de l'EPFL.",
  lastUpdated: 'Dernière mise à jour',
  // Nested translations
  lever: levers,
};
