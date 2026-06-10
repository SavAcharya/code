import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/discover' },
    { path: '/discover', component: () => import('../views/DiscoverView.vue') },
    { path: '/matcher', component: () => import('../views/MatcherView.vue') },
    { path: '/profile', component: () => import('../views/ProfileView.vue') },
    { path: '/tracker', component: () => import('../views/TrackerView.vue') },
    { path: '/cover', component: () => import('../views/CoverView.vue') }
  ]
})

export default router
