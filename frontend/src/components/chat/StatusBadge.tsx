import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

interface Props {
  text: string;
}

export default function StatusBadge({ text }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-300 text-xs font-medium w-fit"
    >
      <Loader2 size={12} className="animate-spin" />
      {text}
    </motion.div>
  );
}
