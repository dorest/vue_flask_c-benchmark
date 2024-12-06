import { createRouter, createWebHistory } from 'vue-router'
import TestCases from '../views/TestCases.vue'
import TestResults from '../views/TestResults.vue'
import ScheduledTasks from '../views/ScheduledTasks.vue'

const routes = [
  {
    path: '/',
    redirect: '/test-cases'
  },
  {
    path: '/test-cases',
    name: 'TestCases',
    component: TestCases
  },
  {
    path: '/results',
    name: 'TestResults',
    component: TestResults
  },
  {
    path: '/results/:id',
    name: 'TestResultDetail',
    component: TestResults,
    props: true
  },
  {
    path: '/schedules',
    name: 'ScheduledTasks',
    component: ScheduledTasks
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 