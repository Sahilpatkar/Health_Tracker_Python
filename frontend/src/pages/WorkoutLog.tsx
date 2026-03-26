import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { getActiveExercises } from '../api/exercises';
import { saveWorkout } from '../api/workouts';
import { Plus, Trash2, Check, CircleHelp } from 'lucide-react';
import {
  HARD_SETS_RULE,
  RPE_DETAILS,
  RPE_TOOLTIP,
  RIR_DETAILS,
  RIR_TOOLTIP,
} from '../copy/trainingTerms';

const MUSCLE_GROUPS = ['All', 'chest', 'back', 'legs', 'shoulders', 'arms', 'core', 'full_body'];

function SetColumnHeader({ label, tooltipText, tipId }: { label: string; tooltipText: string; tipId: string }) {
  return (
    <span className="group relative inline-flex items-center gap-0.5 min-w-0">
      <span>{label}</span>
      <span
        tabIndex={0}
        className="inline-flex shrink-0 cursor-help rounded p-0.5 text-[var(--color-text-muted)] outline-none ring-indigo-500 focus-visible:ring-2"
        aria-describedby={tipId}
      >
        <CircleHelp size={12} aria-hidden />
      </span>
      <span
        id={tipId}
        role="tooltip"
        className="pointer-events-none invisible absolute left-0 top-full z-20 mt-1 w-max max-w-[min(14rem,calc(100vw-2rem))] whitespace-normal rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-2 text-[10px] font-normal leading-snug text-[var(--color-text-muted)] shadow-md group-hover:visible group-focus-within:visible"
      >
        {tooltipText}
      </span>
    </span>
  );
}

interface SetEntry { reps: number; weight: number; rpe: number | null; rir: number | null; }
interface ExEntry { exercise_id: number; exercise_name: string; muscle_group: string; sets: SetEntry[]; }

export default function WorkoutLog() {
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [notes, setNotes] = useState('');
  const [filter, setFilter] = useState('All');
  const [exercises, setExercises] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [sessionExercises, setSessionExercises] = useState<ExEntry[]>([]);
  const [sets, setSets] = useState<SetEntry[]>([{ reps: 0, weight: 0, rpe: null, rir: null }]);

  useEffect(() => {
    getActiveExercises(filter === 'All' ? undefined : filter).then((r) => {
      setExercises(r.data);
      if (r.data.length) setSelectedId(r.data[0].id);
    });
  }, [filter]);

  const addSet = () => setSets([...sets, { reps: 0, weight: 0, rpe: null, rir: null }]);
  const removeSet = (i: number) => setSets(sets.filter((_, idx) => idx !== i));
  const updateSet = (i: number, field: string, value: number | null) =>
    setSets(sets.map((s, idx) => (idx === i ? { ...s, [field]: value } : s)));

  const addExercise = () => {
    const ex = exercises.find((e) => e.id === selectedId);
    if (!ex) return;
    const validSets = sets.filter((s) => s.reps > 0);
    if (!validSets.length) { toast.error('Add at least one set with reps > 0'); return; }
    setSessionExercises([...sessionExercises, {
      exercise_id: ex.id, exercise_name: ex.name, muscle_group: ex.muscle_group, sets: validSets,
    }]);
    setSets([{ reps: 0, weight: 0, rpe: null, rir: null }]);
    toast.success(`Added ${ex.name}`);
  };

  const finishWorkout = async () => {
    if (!sessionExercises.length) { toast.error('Add at least one exercise'); return; }
    try {
      await saveWorkout({
        session_date: date, notes: notes || undefined,
        exercises: sessionExercises.map((ex) => ({
          exercise_id: ex.exercise_id,
          sets: ex.sets.map((s) => ({ reps: s.reps, weight: s.weight, rpe: s.rpe, rir: s.rir })),
        })),
      });
      toast.success('Workout saved!');
      setSessionExercises([]);
    } catch { toast.error('Failed to save'); }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Log Workout</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium mb-1">Date</label>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
                 className="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Notes</label>
          <input type="text" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional"
                 className="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-sm" />
        </div>
      </div>

      <div className="rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 sm:p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Add Exercise</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium mb-1 text-[var(--color-text-muted)]">Muscle Group</label>
            <select value={filter} onChange={(e) => setFilter(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm">
              {MUSCLE_GROUPS.map((mg) => <option key={mg} value={mg}>{mg}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1 text-[var(--color-text-muted)]">Exercise</label>
            <select value={selectedId ?? ''} onChange={(e) => setSelectedId(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm">
              {exercises.map((ex) => <option key={ex.id} value={ex.id}>{ex.name}</option>)}
            </select>
          </div>
        </div>

        <div className="space-y-2 mb-4 -mx-2 px-2 overflow-x-auto overscroll-x-contain">
          <div className="grid grid-cols-[32px_1fr_1fr_1fr_1fr_32px] sm:grid-cols-[40px_1fr_1fr_1fr_1fr_40px] gap-1.5 sm:gap-2 text-xs font-semibold text-[var(--color-text-muted)] items-end min-w-[360px]">
            <span>Set</span>
            <span>Weight</span>
            <span>Reps</span>
            <SetColumnHeader label="RPE" tooltipText={RPE_TOOLTIP} tipId="wk-tip-rpe" />
            <SetColumnHeader label="RIR" tooltipText={RIR_TOOLTIP} tipId="wk-tip-rir" />
            <span />
          </div>
          <AnimatePresence>
            {sets.map((s, i) => (
              <motion.div key={i} initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.2 }}
                          className="grid grid-cols-[32px_1fr_1fr_1fr_1fr_32px] sm:grid-cols-[40px_1fr_1fr_1fr_1fr_40px] gap-1.5 sm:gap-2 items-center min-w-[360px]">
                <span className="text-sm font-medium text-center">{i + 1}</span>
                <input type="number" value={s.weight || ''} onChange={(e) => updateSet(i, 'weight', +e.target.value)} step="2.5" min="0"
                       className="px-2 py-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm w-full" />
                <input type="number" value={s.reps || ''} onChange={(e) => updateSet(i, 'reps', +e.target.value)} min="0"
                       className="px-2 py-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm w-full" />
                <input type="number" value={s.rpe ?? ''} onChange={(e) => updateSet(i, 'rpe', e.target.value ? +e.target.value : null)} step="0.5" min="0" max="10"
                       className="px-2 py-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm w-full" placeholder="-" />
                <input type="number" value={s.rir ?? ''} onChange={(e) => updateSet(i, 'rir', e.target.value ? +e.target.value : null)} min="0" max="10"
                       className="px-2 py-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm w-full" placeholder="-" />
                <button onClick={() => removeSet(i)} className="p-1 text-red-400 hover:text-red-600 transition-colors">
                  <Trash2 size={16} />
                </button>
              </motion.div>
            ))}
          </AnimatePresence>
          <button onClick={addSet} className="flex items-center gap-1 text-sm text-indigo-500 hover:text-indigo-700 font-medium mt-2">
            <Plus size={16} /> Add Set
          </button>
          <details className="mt-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] px-3 py-2 text-xs text-[var(--color-text-muted)]">
            <summary className="cursor-pointer font-medium text-[var(--color-text-muted)] select-none">
              Training terms (RPE &amp; RIR)
            </summary>
            <div className="mt-2 space-y-2 leading-relaxed">
              <p><strong className="text-[var(--color-text)]">RPE.</strong> {RPE_DETAILS}</p>
              <p><strong className="text-[var(--color-text)]">RIR.</strong> {RIR_DETAILS}</p>
              <p><strong className="text-[var(--color-text)]">Hard sets.</strong> {HARD_SETS_RULE}</p>
            </div>
          </details>
        </div>

        <button onClick={addExercise}
                className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition-colors text-sm">
          Add Exercise to Session
        </button>
      </div>

      {sessionExercises.length > 0 && (
        <div className="rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 sm:p-6">
          <h2 className="text-lg font-semibold mb-4">Current Session</h2>
          <div className="space-y-3 mb-4">
            <AnimatePresence>
              {sessionExercises.map((ex, i) => (
                <motion.div key={i} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}
                            className="flex justify-between items-center p-3 rounded-xl bg-[var(--color-surface-dim)]">
                  <div>
                    <p className="font-medium text-sm">{ex.exercise_name}</p>
                    <p className="text-xs text-[var(--color-text-muted)]">{ex.sets.length} sets &middot; {ex.muscle_group}</p>
                  </div>
                  <button onClick={() => setSessionExercises(sessionExercises.filter((_, idx) => idx !== i))}
                          className="text-red-400 hover:text-red-600"><Trash2 size={16} /></button>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
          <button onClick={finishWorkout}
                  className="w-full py-3 rounded-xl bg-green-600 hover:bg-green-700 text-white font-bold transition-colors flex items-center justify-center gap-2">
            <Check size={20} /> Finish & Save Workout
          </button>
        </div>
      )}
    </div>
  );
}
