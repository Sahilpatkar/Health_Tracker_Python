import api from './client';

export const saveBodyMetrics = (data: { date: string; weight_kg: number; waist_cm?: number }) =>
  api.post('/body/metrics', data);

export const getBodyMetrics = () => api.get('/body/metrics');

/** Do not set Content-Type manually — the browser must add the multipart boundary (required for mobile Safari). */
export const uploadPhoto = (formData: FormData) => api.post('/body/photos', formData);

export const getPhotos = () => api.get('/body/photos');

export const deletePhoto = (photoId: number) => api.delete(`/body/photos/${photoId}`);
