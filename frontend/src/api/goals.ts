import api from './client';

export const getGoals = () => api.get('/goals');

export const updateGoals = (data: {
  goal_type: string; calorie_target: number; protein_target: number;
  carb_target: number; fat_target: number; training_days_per_week: number;
}) => api.put('/goals', data);
