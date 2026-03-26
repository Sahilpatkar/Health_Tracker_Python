import { useEffect, useState } from 'react';
import DashboardCard from '../components/DashboardCard';
import ScoreGauge from '../components/ScoreGauge';
import RecommendationCard from '../components/RecommendationCard';
import { getProgressDashboard } from '../api/metrics';

export default function ProgressDashboard() {
  const [data, setData] = useState<any>(null);

  useEffect(() => { getProgressDashboard().then((r) => setData(r.data)); }, []);

  if (!data) return <div className="flex items-center justify-center h-64"><div className="animate-spin w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full" /></div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Progress Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <DashboardCard delay={0}>
          <ScoreGauge score={data.training_score} label="Training" color="#6366f1" />
        </DashboardCard>
        <DashboardCard delay={0.1}>
          <ScoreGauge score={data.nutrition_score} label="Nutrition" color="#22c55e" />
        </DashboardCard>
        <DashboardCard delay={0.2}>
          <ScoreGauge score={data.consistency_score} label="Consistency" color="#f59e0b" />
        </DashboardCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DashboardCard title="PRs This Month" delay={0.3}>
          {data.prs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-left text-[var(--color-text-muted)]">
                  <th className="pb-2">Exercise</th><th className="pb-2">Current 1RM</th><th className="pb-2">Previous</th><th className="pb-2">Change</th>
                </tr></thead>
                <tbody>
                  {data.prs.map((pr: any, i: number) => (
                    <tr key={i} className="border-t border-[var(--color-border)]">
                      <td className="py-2 font-medium">{pr.exercise_name}</td>
                      <td>{pr.current_1rm}</td>
                      <td>{pr.previous_1rm}</td>
                      <td className={pr.improvement > 0 ? 'text-green-500 font-semibold' : pr.improvement < 0 ? 'text-red-500' : ''}>
                        {pr.improvement > 0 ? '+' : ''}{pr.improvement}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="text-[var(--color-text-muted)]">No PR data yet</p>}
        </DashboardCard>

        <DashboardCard title="Recommendations" delay={0.4}>
          <div className="space-y-3">
            {data.recommendations.map((tip: any, i: number) => (
              <RecommendationCard key={i} tip={tip} index={i} />
            ))}
          </div>
        </DashboardCard>
      </div>
    </div>
  );
}
