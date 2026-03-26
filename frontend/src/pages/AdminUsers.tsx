import { useCallback, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import {
  listAdminUsers,
  getAdminUserFood,
  getAdminUserWorkouts,
  getAdminUserGoals,
  getAdminUserMetrics,
  getAdminUserWater,
  getAdminUserPhotos,
  getAdminUserChat,
  getAdminUserMemory,
  getAdminUserPendingActions,
  getPlatformSummary,
} from '../api/admin';

type Tab =
  | 'goals'
  | 'food'
  | 'workouts'
  | 'body'
  | 'water'
  | 'photos'
  | 'chat'
  | 'memory'
  | 'actions';

const TABS: { id: Tab; label: string }[] = [
  { id: 'goals', label: 'Goals' },
  { id: 'food', label: 'Food' },
  { id: 'workouts', label: 'Workouts' },
  { id: 'body', label: 'Body metrics' },
  { id: 'water', label: 'Water' },
  { id: 'photos', label: 'Photos' },
  { id: 'chat', label: 'Chat' },
  { id: 'memory', label: 'Trainer memory' },
  { id: 'actions', label: 'Pending actions' },
];

function fmt(v: unknown): string {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'object') return JSON.stringify(v, null, 2);
  return String(v);
}

export default function AdminUsers() {
  const [users, setUsers] = useState<{ userId: number; user: string; role: string }[]>([]);
  const [summary, setSummary] = useState<Record<string, number> | null>(null);
  const [selected, setSelected] = useState('');
  const [tab, setTab] = useState<Tab>('goals');
  const [foodDate, setFoodDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [payload, setPayload] = useState<unknown>(null);

  useEffect(() => {
    listAdminUsers()
      .then((r) => setUsers(r.data))
      .catch(() => toast.error('Could not load users'));
    getPlatformSummary()
      .then((r) => setSummary(r.data))
      .catch(() => {});
  }, []);

  const loadTab = useCallback(async () => {
    if (!selected) {
      setPayload(null);
      return;
    }
    setLoading(true);
    setPayload(null);
    try {
      let res;
      switch (tab) {
        case 'goals':
          res = await getAdminUserGoals(selected);
          break;
        case 'food':
          res = await getAdminUserFood(selected, foodDate || undefined);
          break;
        case 'workouts':
          res = await getAdminUserWorkouts(selected);
          break;
        case 'body':
          res = await getAdminUserMetrics(selected);
          break;
        case 'water':
          res = await getAdminUserWater(selected);
          break;
        case 'photos':
          res = await getAdminUserPhotos(selected);
          break;
        case 'chat':
          res = await getAdminUserChat(selected);
          break;
        case 'memory':
          res = await getAdminUserMemory(selected);
          break;
        case 'actions':
          res = await getAdminUserPendingActions(selected);
          break;
        default:
          res = { data: null };
      }
      setPayload(res.data);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [selected, tab, foodDate]);

  useEffect(() => {
    loadTab();
  }, [loadTab]);

  const surface = 'rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 sm:p-6';
  const th = 'text-left text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide py-2 px-2';
  const td = 'py-2 px-2 text-sm border-t border-[var(--color-border)] align-top';

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">User data (admin)</h1>
      <p className="text-sm text-[var(--color-text-muted)] mb-6">
        Select a user and category to view their stored health data. Passwords are never shown.
      </p>

      {summary && (
        <div className={`${surface} mb-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-sm`}>
          {Object.entries(summary).map(([k, v]) => (
            <div key={k}>
              <div className="text-[var(--color-text-muted)] text-xs">{k.replace(/_/g, ' ')}</div>
              <div className="font-semibold text-lg">{v}</div>
            </div>
          ))}
        </div>
      )}

      <div className={`${surface} mb-4 space-y-4`}>
        <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
          <div className="flex-1 min-w-0">
            <label className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">User</label>
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm"
            >
              <option value="">Choose a user…</option>
              {users.map((row) => (
                <option key={row.userId} value={row.user}>
                  {row.user} ({row.role})
                </option>
              ))}
            </select>
          </div>
          {tab === 'food' && (
            <div>
              <label className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">Filter date (optional)</label>
              <input
                type="date"
                value={foodDate}
                onChange={(e) => setFoodDate(e.target.value)}
                className="px-3 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm"
              />
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                tab === t.id
                  ? 'bg-indigo-600 text-white'
                  : 'bg-[var(--color-surface-dim)] text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <motion.div
        key={`${selected}-${tab}`}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className={surface}
      >
        {!selected && <p className="text-[var(--color-text-muted)] text-sm">Select a user to load data.</p>}
        {selected && loading && <p className="text-sm text-[var(--color-text-muted)]">Loading…</p>}
        {selected && !loading && tab === 'goals' && (
          <div className="text-sm font-mono whitespace-pre-wrap break-words">
            {payload == null ? 'No goals row for this user.' : fmt(payload)}
          </div>
        )}
        {selected && !loading && tab !== 'goals' && tab !== 'workouts' && Array.isArray(payload) && payload.length === 0 && (
          <p className="text-sm text-[var(--color-text-muted)]">No records.</p>
        )}
        {selected && !loading && tab !== 'goals' && tab !== 'workouts' && Array.isArray(payload) && payload.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse min-w-[640px]">
              <thead>
                <tr>
                  {Object.keys(payload[0] as object).map((col) => (
                    <th key={col} className={th}>
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(payload as Record<string, unknown>[]).map((row, i) => (
                  <tr key={i}>
                    {Object.keys(payload[0] as object).map((col) => (
                      <td key={col} className={`${td} max-w-md`}>
                        <span className="block whitespace-pre-wrap break-words font-mono text-xs">{fmt(row[col])}</span>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {selected && !loading && tab === 'workouts' && Array.isArray(payload) && (
          <div className="space-y-4">
            {(payload as { id: number; session_date: string; notes?: string; sets?: unknown[] }[]).length === 0 && (
              <p className="text-sm text-[var(--color-text-muted)]">No workouts.</p>
            )}
            {(payload as { id: number; session_date: string; notes?: string; sets?: Record<string, unknown>[] }[]).map((s) => (
              <div key={s.id} className="border border-[var(--color-border)] rounded-xl p-4">
                <div className="font-semibold text-sm mb-1">{s.session_date}</div>
                {s.notes && <p className="text-xs text-[var(--color-text-muted)] mb-2">{s.notes}</p>}
                {s.sets && s.sets.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="text-[var(--color-text-muted)]">
                          {Object.keys(s.sets[0]).map((k) => (
                            <th key={k} className="text-left py-1 pr-2">
                              {k}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {s.sets.map((row, j) => (
                          <tr key={j}>
                            {Object.values(row).map((v, k) => (
                              <td key={k} className="py-1 pr-2 border-t border-[var(--color-border)]">
                                {fmt(v)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </motion.div>
    </div>
  );
}
