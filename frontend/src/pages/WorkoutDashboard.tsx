import { useEffect, useState } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import DashboardCard from '../components/DashboardCard';
import { getWorkoutDashboard } from '../api/metrics';
import { HARD_SETS_RULE } from '../copy/trainingTerms';

export default function WorkoutDashboard() {
  const [data, setData] = useState<any>(null);
  const [selectedExercise, setSelectedExercise] = useState('');

  useEffect(() => {
    getWorkoutDashboard().then((r) => {
      setData(r.data);
      if (r.data.exercise_names?.length) setSelectedExercise(r.data.exercise_names[0]);
    });
  }, []);

  if (!data) return <div className="flex items-center justify-center h-64"><div className="animate-spin w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full" /></div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Workout Dashboard</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DashboardCard title="Weekly Workout Count" delay={0}>
          {data.weekly_count.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.weekly_count}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="week" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="workouts" fill="#6366f1" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-[var(--color-text-muted)]">No data yet</p>}
        </DashboardCard>

        <DashboardCard title="Volume Trend (per session)" delay={0.1}>
          {data.volume_trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={data.volume_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="session_date" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="volume" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="text-[var(--color-text-muted)]">No data yet</p>}
        </DashboardCard>

        <DashboardCard title="Top Lift Progress (est. 1RM)" delay={0.2}>
          {data.exercise_names.length > 0 ? (
            <div>
              <select
                value={selectedExercise}
                onChange={(e) => setSelectedExercise(e.target.value)}
                className="mb-3 px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm"
              >
                {data.exercise_names.map((n: string) => <option key={n} value={n}>{n}</option>)}
              </select>
              {data.e1rm_trends[selectedExercise]?.length > 0 && (
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={data.e1rm_trends[selectedExercise]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="session_date" tick={{ fontSize: 12 }} />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="e1rm" stroke="#ec4899" strokeWidth={2} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          ) : <p className="text-[var(--color-text-muted)]">Log workouts to see trends</p>}
        </DashboardCard>

        <DashboardCard title="Hard Sets by Muscle Group" delay={0.3}>
          <p className="text-xs text-[var(--color-text-muted)] mb-3 leading-snug">{HARD_SETS_RULE}</p>
          {data.hard_sets.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.hard_sets}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="muscle_group" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} />
                <Tooltip
                  formatter={(value) => [value as number, 'Hard sets (RPE≥7 or RIR≤3)']}
                />
                <Bar dataKey="hard_sets" fill="#22c55e" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-[var(--color-text-muted)]">Log RPE/RIR to see hard sets</p>}
        </DashboardCard>
      </div>
    </div>
  );
}
