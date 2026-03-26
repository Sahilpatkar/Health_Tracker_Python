import api from './client';

export const saveWorkout = (data: {
  session_date: string;
  notes?: string;
  exercises: Array<{
    exercise_id: number;
    sets: Array<{ reps: number; weight: number; rpe?: number | null; rir?: number | null }>;
  }>;
}) => api.post('/workouts', data);

export const getSessions = (days = 60) =>
  api.get('/workouts/sessions', { params: { days } });
