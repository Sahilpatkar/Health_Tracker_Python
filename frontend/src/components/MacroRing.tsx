import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

export default function MacroRing({ value, target, label, color = '#6366f1' }: { value: number; target: number; label: string; color?: string }) {
  const pct = target > 0 ? Math.min(value / target, 1) : 0;
  const data = [
    { name: 'filled', value: pct },
    { name: 'empty', value: 1 - pct },
  ];

  return (
    <div className="flex flex-col items-center">
      <div className="w-28 h-28 relative">
        <ResponsiveContainer>
          <PieChart>
            <Pie data={data} dataKey="value" innerRadius="70%" outerRadius="90%" startAngle={90} endAngle={-270} paddingAngle={0}>
              <Cell fill={color} />
              <Cell fill="var(--color-border)" />
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-lg font-bold">{Math.round(value)}</span>
        </div>
      </div>
      <span className="text-xs font-medium text-[var(--color-text-muted)] mt-1">{label}</span>
      {target > 0 && <span className="text-xs text-[var(--color-text-muted)]">/ {target}</span>}
    </div>
  );
}
