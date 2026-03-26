import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

export default function DashboardCard({ title, children, delay = 0 }: { title?: string; children: ReactNode; delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 md:p-6 shadow-sm"
    >
      {title && <h3 className="text-sm font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-4">{title}</h3>}
      {children}
    </motion.div>
  );
}
