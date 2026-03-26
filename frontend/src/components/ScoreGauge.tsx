import { motion } from 'framer-motion';

export default function ScoreGauge({ score, label, color = '#6366f1' }: { score: number; label: string; color?: string }) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="128" height="128" viewBox="0 0 128 128">
        <circle cx="64" cy="64" r={r} fill="none" stroke="var(--color-border)" strokeWidth="10" />
        <motion.circle
          cx="64" cy="64" r={r} fill="none"
          stroke={color} strokeWidth="10" strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={circ}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
          transform="rotate(-90 64 64)"
        />
        <text x="64" y="64" textAnchor="middle" dominantBaseline="central"
              className="text-2xl font-bold" fill="var(--color-text)" fontSize="28">
          {score}
        </text>
      </svg>
      <span className="text-sm font-medium text-[var(--color-text-muted)]">{label}</span>
    </div>
  );
}
