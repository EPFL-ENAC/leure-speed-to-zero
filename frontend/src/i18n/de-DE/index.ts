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
  // Navigation
  home: 'Startseite',
  about: 'Über uns',
  legal: 'Rechtliches',
  launchApp: 'Rechner öffnen',
  openCalculator: 'Rechner öffnen',
  tryCalculator: 'Rechner ausprobieren',
  allRightsReserved: 'Alle Rechte vorbehalten',
  learnMore: 'Mehr erfahren',
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
  keyMetrics: 'Schlüsselkennzahlen',
  // Chart components
  loadingChartData: 'Diagrammdaten werden geladen...',
  retry: 'Erneut versuchen',
  noChartDataAvailable: 'Keine Diagrammdaten verfügbar',
  noDataAvailable: 'Keine Daten verfügbar',
  downloadCSV: 'CSV herunterladen',
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
  // Home Page
  welcomeToSpeedToZero: 'Willkommen bei Speed to Zero',
  homeSubtitle: 'Interaktiver Klimaneutralitätsrechner für die Schweiz',
  exploreBySector: 'Nach Sektor erkunden',
  selectSector: 'Sektor auswählen',
  selectSectorDesc: 'Wählen Sie aus Gebäude, Verkehr, Landwirtschaft oder Forstwirtschaft',
  adjustLevers: 'Politische Hebel anpassen',
  adjustLeversDesc: 'Konfigurieren Sie Maßnahmen und sehen Sie ihre Auswirkungen in Echtzeit',
  analyzeResults: 'Ergebnisse analysieren',
  analyzeResultsDesc: 'Visualisieren Sie Emissionen, Energieverbrauch und Leistungskennzahlen',
  // About Page
  aboutTitle: 'Über Speed to Zero',
  ourMission: 'Unsere Mission',
  ourMissionDesc:
    'Speed to Zero ist ein umfassendes Modellierungstool für Klimaneutralität, das Entscheidungsträgern, Forschern und Organisationen helfen soll, Wege zur Erreichung von Netto-Null-Emissionen zu erkunden. Unsere Mission ist es, transparente, datengestützte Einblicke in die komplexen Übergänge zu bieten, die in mehreren Wirtschaftssektoren erforderlich sind.',
  whatWeOffer: 'Was wir bieten',
  whatWeOfferDesc:
    'Unsere Plattform bietet detaillierte Modellierung und Analyse in Schlüsselsektoren:',
  buildingsSector: 'Gebäudesektor',
  buildingsSectorDesc:
    'Modellieren Sie Heizung, Kühlung und Energieeffizienzverbesserungen in Wohn- und Gewerbegebäuden',
  transportSector: 'Verkehrssektor',
  transportSectorDesc:
    'Analysieren Sie Übergänge zu Elektrofahrzeugen, öffentlichen Verkehrsmitteln und nachhaltiger Mobilität',
  agricultureSector: 'Landwirtschaftssektor',
  agricultureSectorDesc:
    'Erkunden Sie nachhaltige Landwirtschaftspraktiken und Emissionsreduktionsstrategien',
  forestrySector: 'Forstwirtschaftssektor',
  forestrySectorDesc:
    'Verstehen Sie das Kohlenstoffbindungspotenzial und nachhaltige Forstwirtschaft',
  howItWorks: 'Wie es funktioniert',
  howItWorksDesc:
    'Speed to Zero verwendet eine ausgeklügelte Modellierungs-Engine, mit der Sie politische Hebel anpassen und sofort die Auswirkungen auf Emissionen, Energieverbrauch und andere wichtige Kennzahlen sehen können. Der Rechner kombiniert historische Daten mit zukunftsorientierten Szenarien, um umfassende Einblicke in potenzielle Wege zur Klimaneutralität zu bieten.',
  theTeam: 'Das Team',
  theTeamDesc:
    'Speed to Zero wird von der EPFL (École polytechnique fédérale de Lausanne) entwickelt und gepflegt und vereint Expertise in Klimawissenschaft, Energiesystemen und Datenvisualisierung.',
  startExploring: 'Erkunden beginnen',
  // Legal Page
  legalNotice: 'Rechtliche Hinweise',
  termsOfUse: 'Nutzungsbedingungen',
  termsOfUseDesc:
    'Durch den Zugriff auf und die Nutzung von Speed to Zero stimmen Sie diesen Nutzungsbedingungen zu. Dieser Rechner wird zu Informations- und Forschungszwecken bereitgestellt. Obwohl wir uns um Genauigkeit bemühen, sollten die Prognosen und Modelle nicht als alleinige Grundlage für politische oder Investitionsentscheidungen verwendet werden.',
  privacyPolicy: 'Datenschutzrichtlinie',
  privacyPolicyDesc:
    'Wir respektieren Ihre Privatsphäre. Speed to Zero sammelt keine persönlichen Informationen, es sei denn, Sie stellen sie ausdrücklich zur Verfügung. Alle Daten, die Sie in den Rechner eingeben, bleiben auf Ihrem Gerät und werden ohne Ihre Zustimmung nicht an unsere Server übertragen.',
  dataUsage: 'Datennutzung',
  dataUsageDesc:
    'Die in unseren Modellen verwendeten Daten stammen aus öffentlich zugänglichen Quellen, einschließlich Eurostat, nationalen Statistikämtern und Forschungsinstituten. Alle Datenquellen sind in der Anwendung dokumentiert und referenziert.',
  disclaimer: 'Haftungsausschluss',
  disclaimerDesc:
    'Die von Speed to Zero bereitgestellten Modelle und Prognosen basieren auf Annahmen und historischen Daten. Die tatsächlichen Ergebnisse können erheblich abweichen. Die EPFL und die Projektbeitragenden haften nicht für Entscheidungen, die auf Grundlage der von diesem Rechner bereitgestellten Informationen getroffen werden.',
  intellectualProperty: 'Geistiges Eigentum',
  intellectualPropertyDesc:
    'Speed to Zero ist Open-Source-Software. Der Code und die Methodik stehen zur Überprüfung und Mitwirkung zur Verfügung. Bitte beachten Sie unser GitHub-Repository für Lizenzdetails.',
  contact: 'Kontakt',
  contactDesc:
    'Für Fragen, Feedback oder Kooperationsmöglichkeiten kontaktieren Sie uns bitte über die Website der EPFL ENAC-Fakultät.',
  lastUpdated: 'Zuletzt aktualisiert',
  // Welcome Popup
  welcomePopup: {
    subtitle: 'Interaktiver Klimaneutralitätsrechner für die Schweiz',
    description:
      'Erkunden Sie Wege zur Netto-Null-Emission, indem Sie politische Hebel anpassen und deren Auswirkungen auf verschiedene Sektoren visualisieren.',
    featureLevers: 'Passen Sie Hebel an, um Interventionen zu modellieren',
    featureVisualize: 'Visualisieren Sie Emissionen und Energiekennzahlen',
    featureCompare: 'Vergleichen Sie Szenarien über Sektoren hinweg',
    dontShowAgain: 'Nicht mehr anzeigen',
    startTutorial: 'Tutorial starten',
    skipTutorial: 'Überspringen',
  },
  // Tour translations
  tour: {
    sectors:
      'Willkommen! Wählen Sie zunächst einen Sektor aus diesem Menü. Jeder Sektor enthält detaillierte Unterregisterkarten mit Diagrammen und Analysen.',
    levers:
      'Dies sind politische Hebel. Passen Sie sie an, um zu sehen, wie verschiedene Interventionen die Ergebnisse beeinflussen. Klicken Sie zum Erweitern und detaillierte Optionen anzuzeigen.',
    kpis: 'Die wichtigsten Leistungsindikatoren zeigen die Hauptmetriken für den ausgewählten Sektor. Sie werden in Echtzeit aktualisiert, wenn Sie die Hebel anpassen.',
    charts:
      'Hier erscheinen detaillierte Diagramme und Visualisierungen. Sie bieten eine eingehende Analyse von Emissionen, Energieverbrauch und anderen Metriken.',
    skip: 'Überspringen',
    next: 'Weiter',
    back: 'Zurück',
    finish: 'Verstanden!',
  },
  // Nested translations
  lever: levers,
};
