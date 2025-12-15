import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  // Redirect root to overall sector
  {
    path: '/',
    redirect: '/overall',
  },

  // Main Layout Routes (About, Legal)
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: 'about',
        name: 'about',
        component: () => import('src/pages/AboutPage.vue'),
      },
      {
        path: 'legal',
        name: 'legal',
        component: () => import('src/pages/LegalPage.vue'),
      },
    ],
  },

  // Dashboard Layout Routes (Application)
  {
    path: '/',
    component: () => import('layouts/DashboardLayout.vue'),
    children: [
      {
        path: 'buildings/:subtab?',
        name: 'buildings',
        component: () => import('src/pages/sectors/BuildingsTab.vue'),
      },
      {
        path: 'transport/:subtab?',
        name: 'transport',
        component: () => import('src/pages/sectors/TransportTab.vue'),
      },
      {
        path: 'energy/:subtab?',
        name: 'energy',
        component: () => import('pages/EnergyTab.vue'),
      },
      {
        path: 'forestry/:subtab?',
        name: 'forestry',
        component: () => import('src/pages/sectors/ForestryTab.vue'),
      },
      {
        path: 'agriculture/:subtab?',
        name: 'agriculture',
        component: () => import('src/pages/sectors/AgricultureTab.vue'),
      },
      {
        path: 'overall/:subtab?',
        name: 'overall',
        component: () => import('src/pages/sectors/OverallTab.vue'),
      },
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
