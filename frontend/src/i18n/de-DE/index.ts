import levers from './levers';

export default {
  failed: 'Aktion fehlgeschlagen',
  success: 'Aktion erfolgreich',
  // Common UI elements
  welcome: 'Willkommen bei Speed to Zero',
  loading: 'Wird geladen...',
  save: 'Speichern',
  cancel: 'Abbrechen',
  delete: 'Löschen',
  edit: 'Bearbeiten',
  close: 'Schließen',
  submit: 'Absenden',
  resetDefault: 'Auf Standard zurücksetzen',
  // Component-specific translations
  levers: 'Hebel',
  leverDetails: 'Hebeldetails',
  selectPathway: 'Pfad auswählen',
  featureNotReady: 'Funktion noch nicht verfügbar',
  runModel: 'Modell ausführen',
  runModelToSeeData: 'Führen Sie das Modell aus, um {sector}-Daten anzuzeigen',
  clickToView: 'Klicken Sie hier, um {title}-Daten anzuzeigen',
  backToOverview: 'Zurück zur Übersicht',
  selectKpiToViewDetails:
    'Wählen Sie einen KPI aus, um detaillierte Diagramme und Analysen anzuzeigen',
  showMoreInformation: 'Weitere Informationen anzeigen',
  // Chart components
  loadingChartData: 'Diagrammdaten werden geladen...',
  retry: 'Erneut versuchen',
  noChartDataAvailable: 'Keine Diagrammdaten verfügbar',
  noDataAvailable: 'Keine Daten verfügbar',
  // Time periods
  historical: 'Historisch',
  forecast: 'Prognose',
  // KPI translations
  kpi: {
    status: {
      excellent: 'Ausgezeichnet',
      warning: 'Warnung',
      danger: 'Gefahr',
    },
    higherIsBetter: 'Höher ist besser',
    lowerIsBetter: 'Niedriger ist besser',
    clickToViewDetails: 'Klicken Sie hier, um detaillierte Diagramme anzuzeigen',
  },
  // Nested translations
  lever: levers,
};
