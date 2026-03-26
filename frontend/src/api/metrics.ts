import api from './client';

export const getWorkoutDashboard = () => api.get('/metrics/workout-dashboard');
export const getNutritionDashboard = () => api.get('/metrics/nutrition-dashboard');
export const getProgressDashboard = () => api.get('/metrics/progress-dashboard');
