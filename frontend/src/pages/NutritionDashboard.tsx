import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import DashboardCard from '../components/DashboardCard';
import MacroRing from '../components/MacroRing';
import { getNutritionDashboard } from '../api/metrics';

export default function NutritionDashboard() {
  const [data, setData] = useState<any>(null);

  useEffect(() => { getNutritionDashboard().then((r) => setData(r.data)); }, []);

  if (!data) return <div className="flex items-center justify-center h-64"><div className="animate-spin w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full" /></div>;

  const today = data.daily_macros.length > 0 ? data.daily_macros[data.daily_macros.length - 1] : { calories: 0, protein: 0, fat: 0, carbs: 0 };

  const weeklyData = (() => {
    const weeks: Record<string, { cal: number[]; prot: number[]; fat: number[]; carbs: number[] }> = {};
    data.daily_macros.forEach((d: any) => {
      const dt = new Date(d.date);
      const wk = `${dt.getFullYear()}-W${String(Math.ceil((dt.getDate() + new Date(dt.getFullYear(), dt.getMonth(), 1).getDay()) / 7)).padStart(2, '0')}`;
      if (!weeks[wk]) weeks[wk] = { cal: [], prot: [], fat: [], carbs: [] };
      weeks[wk].cal.push(d.calories); weeks[wk].prot.push(d.protein);
      weeks[wk].fat.push(d.fat); weeks[wk].carbs.push(d.carbs);
    });
    return Object.entries(weeks).map(([wk, v]) => ({
      week: wk,
      calories: Math.round(v.cal.reduce((a, b) => a + b, 0) / v.cal.length),
      protein: Math.round(v.prot.reduce((a, b) => a + b, 0) / v.prot.length),
      fat: Math.round(v.fat.reduce((a, b) => a + b, 0) / v.fat.length),
      carbs: Math.round(v.carbs.reduce((a, b) => a + b, 0) / v.carbs.length),
    }));
  })();

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Nutrition Dashboard</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <DashboardCard title="Today's Intake" delay={0}>
          <div className="flex justify-around">
            <MacroRing value={today.calories} target={data.calorie_target} label="Calories" color="#6366f1" />
            <MacroRing value={today.protein} target={data.protein_target} label="Protein (g)" color="#22c55e" />
          </div>
        </DashboardCard>

        <DashboardCard title="7-Day Adherence" delay={0.1}>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Calorie adherence</span>
                <span className="font-semibold">{Math.round(data.calorie_adherence * 100)}%</span>
              </div>
              <div className="h-3 rounded-full bg-[var(--color-surface-dim)]">
                <div className="h-3 rounded-full bg-indigo-500 transition-all" style={{ width: `${data.calorie_adherence * 100}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Protein adherence</span>
                <span className="font-semibold">{Math.round(data.protein_adherence * 100)}%</span>
              </div>
              <div className="h-3 rounded-full bg-[var(--color-surface-dim)]">
                <div className="h-3 rounded-full bg-green-500 transition-all" style={{ width: `${data.protein_adherence * 100}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Meal log consistency</span>
                <span className="font-semibold">{Math.round(data.food_logging_adherence * 100)}%</span>
              </div>
              <div className="h-3 rounded-full bg-[var(--color-surface-dim)]">
                <div className="h-3 rounded-full bg-amber-500 transition-all" style={{ width: `${data.food_logging_adherence * 100}%` }} />
              </div>
            </div>
          </div>
        </DashboardCard>

        <DashboardCard title="Weekly Macro Averages" delay={0.2}>
          {weeklyData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={weeklyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="week" tick={{ fontSize: 10 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="protein" fill="#22c55e" radius={[4, 4, 0, 0]} />
                <Bar dataKey="fat" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                <Bar dataKey="carbs" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-[var(--color-text-muted)]">No data yet</p>}
        </DashboardCard>
      </div>
    </div>
  );
}
