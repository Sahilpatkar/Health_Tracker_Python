import api from './client';

const u = (username: string) => encodeURIComponent(username);

export const listAdminUsers = () => api.get(`/admin/users`);

export const getAdminUserFood = (username: string, date?: string) =>
  api.get(`/admin/users/${u(username)}/food`, { params: date ? { date } : undefined });

export const getAdminUserWorkouts = (username: string) =>
  api.get(`/admin/users/${u(username)}/workouts`);

export const getAdminUserGoals = (username: string) =>
  api.get(`/admin/users/${u(username)}/goals`);

export const getAdminUserMetrics = (username: string) =>
  api.get(`/admin/users/${u(username)}/metrics`);

export const getAdminUserWater = (username: string) =>
  api.get(`/admin/users/${u(username)}/water`);

export const getAdminUserPhotos = (username: string) =>
  api.get(`/admin/users/${u(username)}/photos`);

export const getAdminUserChat = (username: string) =>
  api.get(`/admin/users/${u(username)}/chat`);

export const getAdminUserMemory = (username: string) =>
  api.get(`/admin/users/${u(username)}/memory`);

export const getAdminUserPendingActions = (username: string) =>
  api.get(`/admin/users/${u(username)}/pending-actions`);

export const getPlatformSummary = () => api.get('/admin/summary');
