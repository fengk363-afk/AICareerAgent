import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import DashboardView from '../views/DashboardView.vue'
import ResumeView from '../views/ResumeView.vue'
import JobsView from '../views/JobsView.vue'
import ApplicationsView from '../views/ApplicationsView.vue'
import ProfileView from '../views/ProfileView.vue'
import InterviewView from '../views/InterviewView.vue'
import AgentView from '../views/AgentView.vue'
import LearningView from '../views/LearningView.vue'
import CompanyView from '../views/CompanyView.vue'
import GoalsView from '../views/GoalsView.vue'
import JobDetailView from '../views/JobDetailView.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'Login', component: LoginView },
  { path: '/register', name: 'Register', component: RegisterView },
  {
    path: '/home',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/resume',
    name: 'Resume',
    component: ResumeView,
    meta: { requiresAuth: true }
  },
  {
    path: '/jobs',
    name: 'Jobs',
    component: JobsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/jobs/:id',
    name: 'JobDetail',
    component: JobDetailView,
    meta: { requiresAuth: true }
  },
  {
    path: '/applications',
    name: 'Applications',
    component: ApplicationsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/interview',
    name: 'Interview',
    component: InterviewView,
    meta: { requiresAuth: true }
  },
  {
    path: '/agent',
    name: 'Agent',
    component: AgentView,
    meta: { requiresAuth: true }
  },
  {
    path: '/learning',
    name: 'Learning',
    component: LearningView,
    meta: { requiresAuth: true }
  },
  {
    path: '/company',
    name: 'Company',
    component: CompanyView,
    meta: { requiresAuth: true }
  },
  {
    path: '/goals',
    name: 'Goals',
    component: GoalsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: ProfileView,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    next('/home')
  } else {
    next()
  }
})

export default router
