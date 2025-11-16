import Shepherd from 'shepherd.js';
import 'shepherd.js/dist/css/shepherd.css';
import { useI18n } from 'vue-i18n';

export function useTour() {
  const { t } = useI18n();

  const createTour = () => {
    const tour = new Shepherd.Tour({
      useModalOverlay: true,
      defaultStepOptions: {
        cancelIcon: { enabled: true },
        classes: 'shepherd-theme-custom',
        scrollTo: { behavior: 'smooth', block: 'center' },
      },
    });

    tour.addStep({
      id: 'sectors',
      text: t('tour.sectors'),
      attachTo: { element: '.vertical-nav-drawer', on: 'right' },
      buttons: [
        {
          text: t('tour.skip'),
          action: () => void tour.cancel(),
          secondary: true,
        },
        {
          text: t('tour.next'),
          action: () => void tour.next(),
        },
      ],
    });

    tour.addStep({
      id: 'levers',
      text: t('tour.levers'),
      attachTo: { element: '.levers-col', on: 'left' },
      buttons: [
        {
          text: t('tour.back'),
          action: () => void tour.back(),
          secondary: true,
        },
        {
          text: t('tour.next'),
          action: () => void tour.next(),
        },
      ],
    });

    tour.addStep({
      id: 'kpis',
      text: t('tour.kpis'),
      attachTo: { element: '.top-kpis-bar', on: 'bottom' },
      buttons: [
        {
          text: t('tour.back'),
          action: () => void tour.back(),
          secondary: true,
        },
        {
          text: t('tour.next'),
          action: () => void tour.next(),
        },
      ],
    });

    tour.addStep({
      id: 'charts',
      text: t('tour.charts'),
      attachTo: { element: '.charts-content', on: 'top' },
      buttons: [
        {
          text: t('tour.back'),
          action: () => void tour.back(),
          secondary: true,
        },
        {
          text: t('tour.finish'),
          action: () => void tour.complete(),
        },
      ],
    });

    return tour;
  };

  const startTour = () => {
    const hasSeenTour = localStorage.getItem('hasSeenTour');
    if (!hasSeenTour) {
      const tour = createTour();
      void tour.start();
      tour.on('complete', () => {
        localStorage.setItem('hasSeenTour', 'true');
      });
      tour.on('cancel', () => {
        localStorage.setItem('hasSeenTour', 'true');
      });
    }
  };

  return { startTour };
}
