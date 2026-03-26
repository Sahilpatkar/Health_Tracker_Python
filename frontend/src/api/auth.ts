import api from './client';

export const login = (username: string, password: string) =>
  api.post('/auth/login', { username, password });

export const register = (username: string, password: string) =>
  api.post('/auth/register', { username, password });

export const getMe = () => api.get('/auth/me');
