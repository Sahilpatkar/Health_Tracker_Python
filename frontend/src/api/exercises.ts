import api from './client';

export const getActiveExercises = (muscle_group?: string) =>
  api.get('/exercises', { params: muscle_group ? { muscle_group } : {} });

export const getAllExercises = () => api.get('/exercises/all');

export const createExercise = (data: { name: string; muscle_group: string; equipment: string }) =>
  api.post('/exercises', data);

export const updateExercise = (id: number, data: Record<string, unknown>) =>
  api.put(`/exercises/${id}`, data);

export const deleteExercise = (id: number) => api.delete(`/exercises/${id}`);
