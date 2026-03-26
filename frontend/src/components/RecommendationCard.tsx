import { motion } from 'framer-motion';
import { Lightbulb } from 'lucide-react';

interface Tip { category: string; message: string; }

export default function RecommendationCard({ tip, index }: { tip: Tip; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.35, delay: index * 0.1 }}
      className="flex gap-3 p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/30 border border-indigo-200 dark:border-indigo-800"
    >
      <Lightbulb className="w-5 h-5 text-indigo-500 shrink-0 mt-0.5" />
      <div>
        <p className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase">{tip.category}</p>
        <p className="text-sm mt-1">{tip.message}</p>
      </div>
    </motion.div>
  );
}
