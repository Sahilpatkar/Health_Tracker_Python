import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../hooks/useAuth';
import {
  Dumbbell, Utensils, TrendingUp, Camera,
  Settings, ShieldCheck, Users, LogOut, ChevronLeft, ChevronRight,
  LayoutDashboard, Apple, MessageCircle, X,
} from 'lucide-react';
import { useEffect, useState } from 'react';

const navItems = [
  { to: '/workout', icon: LayoutDashboard, label: 'Workout Dashboard' },
  { to: '/workout/log', icon: Dumbbell, label: 'Log Workout' },
  { to: '/nutrition', icon: Apple, label: 'Nutrition Dashboard' },
  { to: '/nutrition/log', icon: Utensils, label: 'Log Food & Water' },
  { to: '/progress', icon: TrendingUp, label: 'Progress' },
  { to: '/body', icon: Camera, label: 'Body Progress' },
  { to: '/settings', icon: Settings, label: 'Goals & Settings' },
  { to: '/chat', icon: MessageCircle, label: 'AI Trainer' },
];

const adminItems = [
  { to: '/admin/users', icon: Users, label: 'User data' },
  { to: '/admin/exercises', icon: ShieldCheck, label: 'Exercise Catalog' },
];

interface SidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export default function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  useEffect(() => {
    onMobileClose();
  }, [location.pathname]); // eslint-disable-line react-hooks/exhaustive-deps

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
      isActive
        ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300'
        : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-dim)] hover:text-[var(--color-text)]'
    }`;

  const sidebarContent = (
    <>
      <div className="flex items-center justify-between px-4 py-5 border-b border-[var(--color-border)]">
        {!collapsed && (
          <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-lg font-bold bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">
            Health Tracker
          </motion.span>
        )}
        <button onClick={() => setCollapsed(!collapsed)} className="hidden md:block p-1.5 rounded-lg hover:bg-[var(--color-surface-dim)] text-[var(--color-text-muted)]">
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
        <button onClick={onMobileClose} className="md:hidden p-1.5 rounded-lg hover:bg-[var(--color-surface-dim)] text-[var(--color-text-muted)]">
          <X size={20} />
        </button>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto overscroll-contain">
        {navItems.map((item) => (
          <NavLink key={item.to} to={item.to} className={linkClass}>
            <item.icon size={20} className="shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
        {user?.role === 'admin' && (
          <>
            <div className="my-3 border-t border-[var(--color-border)]" />
            {adminItems.map((item) => (
              <NavLink key={item.to} to={item.to} className={linkClass}>
                <item.icon size={20} className="shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      <div className="px-3 py-4 border-t border-[var(--color-border)]">
        {!collapsed && user && (
          <p className="text-xs text-[var(--color-text-muted)] mb-2 px-3 truncate">
            {user.username} ({user.role})
          </p>
        )}
        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 w-full transition-colors"
        >
          <LogOut size={20} className="shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <motion.aside
        animate={{ width: collapsed ? 72 : 256 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="hidden md:flex h-screen sticky top-0 flex-col bg-[var(--color-surface)] border-r border-[var(--color-border)] overflow-hidden"
      >
        {sidebarContent}
      </motion.aside>

      {/* Mobile drawer overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 bg-black/50 z-40 md:hidden"
              onClick={onMobileClose}
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="fixed inset-y-0 left-0 z-50 w-[280px] flex flex-col bg-[var(--color-surface)] border-r border-[var(--color-border)] overflow-hidden md:hidden safe-area-inset"
            >
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
