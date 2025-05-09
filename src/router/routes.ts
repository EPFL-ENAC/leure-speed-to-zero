import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('layouts/DashboardLayout.vue'),
    children: [
      { path: '', component: () => import('pages/EmissionsPage.vue') },
      { path: 'energy', component: () => import('pages/EnergyPage.vue') },
      { path: 'test-api', component: () => import('pages/ApiTestPage.vue') },
      {
        path: 'buildings/:subtab?',
        name: 'buildings',
        component: () => import('pages/BuildingsTab.vue'),
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
