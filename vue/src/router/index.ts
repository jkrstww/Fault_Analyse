import { createRouter, createWebHistory } from 'vue-router';
import HistoryRecord from '../views/HistoryRecord.vue';
import MainPart from '../components/MainPart.vue'
import TestOne from '../components/TestOne.vue'
import TestTwo from '../views/TestTwo.vue'

const routes = [
  {
    path: '/',
    name: 'Main',
    component: TestOne
  },
  {
    path: '/historyRecord',
    name: 'HistoryRecord',
    component: HistoryRecord,
  },
  {
    path: '/test1',
    name: 'Test1',
    component: TestOne
  },
  {
    path: '/test2',
    name: 'Test2',
    component: TestTwo
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;