import { WifiOff } from 'lucide-react'
import { AnimatePresence, motion } from 'framer-motion'
import { useOnlineStatus } from '../hooks/useOnlineStatus'

export default function OfflineBanner() {
  const isOnline = useOnlineStatus()

  return (
    <AnimatePresence>
      {!isOnline && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.25 }}
          className="overflow-hidden"
        >
          <div className="flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium bg-amber-500/15 text-amber-400 border-b border-amber-500/20">
            <WifiOff size={16} />
            <span>You're offline — showing cached data</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
