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
        component: () => import('pages/BuildingsTab.vue'),
      },
      {
        path: 'transport/:subtab?',
        name: 'transport',
        component: () => import('pages/TransportTab.vue'),
      },
      {
        path: 'forestry/:subtab?',
        name: 'forestry',
        component: () => import('pages/ForestryTab.vue'),
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
