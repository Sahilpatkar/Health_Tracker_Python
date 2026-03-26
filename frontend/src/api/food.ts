import api from './client';

export const getFoodItems = () => api.get('/food/items');

export const addFoodIntake = (data: {
  food_id: number; date: string; meal_type: string;
  food_item: string; quantity: number; unit: string;
}) => api.post('/food/intake', data);

export const deleteFoodIntake = (id: number) => api.delete(`/food/intake/${id}`);

export const getFoodIntake = (days = 30) =>
  api.get('/food/intake', { params: { days } });

export const addWater = (data: { date: string; water_intake: number }) =>
  api.post('/food/water', data);

export const getWater = (days = 30) =>
  api.get('/food/water', { params: { days } });
