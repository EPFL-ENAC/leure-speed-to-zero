import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('layouts/DashboardLayout.vue'),
    children: [
      { path: '', redirect: '/buildings' }, // Redirect to default sector
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
