import api from './client';

export const saveBodyMetrics = (data: { date: string; weight_kg: number; waist_cm?: number }) =>
  api.post('/body/metrics', data);

export const getBodyMetrics = () => api.get('/body/metrics');

export const uploadPhoto = (formData: FormData) =>
  api.post('/body/photos', formData, { headers: { 'Content-Type': 'multipart/form-data' } });

export const getPhotos = () => api.get('/body/photos');
