import { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, X, Dumbbell, Target, Utensils } from 'lucide-react';
import toast from 'react-hot-toast';
import { confirmAction, rejectAction, type ActionData } from '../../api/chat';

interface Props {
  action: ActionData;
  onResolved: (actionId: number, status: 'confirmed' | 'rejected') => void;
}

const ICONS: Record<string, typeof Dumbbell> = {
  create_workout: Dumbbell,
  update_goals: Target,
  log_food: Utensils,
  log_water: Utensils,
};

export default function ActionCard({ action, onResolved }: Props) {
  const [loading, setLoading] = useState(false);
  const [resolved, setResolved] = useState<'confirmed' | 'rejected' | null>(null);

  const Icon = ICONS[action.action_type] || Target;
  const d = action.display_data;

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await confirmAction(action.action_id);
      setResolved('confirmed');
      onResolved(action.action_id, 'confirmed');
      toast.success('Action applied!');
    } catch {
      toast.error('Failed to confirm action');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    setLoading(true);
    try {
      await rejectAction(action.action_id);
      setResolved('rejected');
      onResolved(action.action_id, 'rejected');
    } catch {
      toast.error('Failed to reject action');
    } finally {
      setLoading(false);
    }
  };

  const title =
    action.action_type === 'create_workout'
      ? 'Workout Plan'
      : action.action_type === 'update_goals'
        ? 'Goal Update'
        : action.action_type === 'log_food'
          ? 'Food Log'
          : 'Action';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-dim)] overflow-hidden max-w-md"
    >
      <div className="flex items-center gap-2 px-4 py-2.5 bg-[var(--color-surface)] border-b border-[var(--color-border)]">
        <Icon size={16} className="text-indigo-500" />
        <span className="text-sm font-semibold">{title}</span>
        {resolved && (
          <span
            className={`ml-auto text-xs font-medium px-2 py-0.5 rounded-full ${
              resolved === 'confirmed'
                ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300'
                : 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300'
            }`}
          >
            {resolved === 'confirmed' ? 'Applied' : 'Dismissed'}
          </span>
        )}
      </div>

      <div className="px-4 py-3 text-sm space-y-2">
        {action.action_type === 'create_workout' && (
          <>
            {d.session_date && (
              <p className="text-xs text-[var(--color-text-muted)]">Date: {d.session_date as string}</p>
            )}
            {d.notes && <p className="text-xs text-[var(--color-text-muted)]">{d.notes as string}</p>}
            <table className="w-full text-xs">
              <thead>
                <tr className="text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                  <th className="text-left py-1">Exercise</th>
                  <th className="text-center py-1">Sets</th>
                  <th className="text-center py-1">Reps</th>
                  <th className="text-center py-1">Weight</th>
                </tr>
              </thead>
              <tbody>
                {(d.exercises as Array<{exercise_name: string; sets: Array<{reps: number; weight?: number}>}>)?.map((ex, i) => (
                  <tr key={i} className="border-b border-[var(--color-border)] last:border-0">
                    <td className="py-1.5 font-medium">{ex.exercise_name}</td>
                    <td className="text-center">{ex.sets.length}</td>
                    <td className="text-center">{ex.sets.map(s => s.reps).join('/')}</td>
                    <td className="text-center">{ex.sets[0]?.weight ? `${ex.sets[0].weight}kg` : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        {action.action_type === 'update_goals' && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            {d.goal_type != null && String(d.goal_type) !== '' ? (
              <div>
                <span className="text-[var(--color-text-muted)]">Goal:</span> {String(d.goal_type).replace('_', ' ')}
              </div>
            ) : null}
            {d.calorie_target != null ? (
              <div>
                <span className="text-[var(--color-text-muted)]">Calories:</span> {Number(d.calorie_target)} kcal
              </div>
            ) : null}
            {d.protein_target != null ? (
              <div>
                <span className="text-[var(--color-text-muted)]">Protein:</span> {Number(d.protein_target)}g
              </div>
            ) : null}
            {d.carb_target != null ? (
              <div>
                <span className="text-[var(--color-text-muted)]">Carbs:</span> {Number(d.carb_target)}g
              </div>
            ) : null}
            {d.fat_target != null ? (
              <div>
                <span className="text-[var(--color-text-muted)]">Fat:</span> {Number(d.fat_target)}g
              </div>
            ) : null}
            {d.training_days_per_week != null ? (
              <div>
                <span className="text-[var(--color-text-muted)]">Training days:</span> {Number(d.training_days_per_week)}/week
              </div>
            ) : null}
          </div>
        )}

        {action.action_type === 'log_food' && (() => {
          type FoodItem = { food_item: string; quantity: number; unit: string; calories: number; protein: number; fat: number; carbs: number };
          const items = (d.items as FoodItem[] | undefined) ?? (d.food_item != null ? [{
            food_item: String(d.food_item), quantity: Number(d.quantity), unit: String(d.unit),
            calories: 0, protein: 0, fat: 0, carbs: 0,
          }] : []);
          const totals = items.reduce(
            (acc, it) => ({ cal: acc.cal + it.calories, pro: acc.pro + it.protein, fat: acc.fat + it.fat, carb: acc.carb + it.carbs }),
            { cal: 0, pro: 0, fat: 0, carb: 0 },
          );
          return (
            <>
              <div className="flex gap-3 text-xs text-[var(--color-text-muted)] mb-1">
                {d.date != null ? <span>Date: {String(d.date)}</span> : null}
                {d.meal_type != null ? <span>Meal: {String(d.meal_type)}</span> : null}
              </div>
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                    <th className="text-left py-1">Item</th>
                    <th className="text-center py-1">Qty</th>
                    <th className="text-right py-1">Cal</th>
                    <th className="text-right py-1">P</th>
                    <th className="text-right py-1">F</th>
                    <th className="text-right py-1">C</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((it, i) => (
                    <tr key={i} className="border-b border-[var(--color-border)] last:border-0">
                      <td className="py-1.5 font-medium">{it.food_item}</td>
                      <td className="text-center">{it.quantity} {it.unit}</td>
                      <td className="text-right">{Math.round(it.calories)}</td>
                      <td className="text-right">{Math.round(it.protein)}g</td>
                      <td className="text-right">{Math.round(it.fat)}g</td>
                      <td className="text-right">{Math.round(it.carbs)}g</td>
                    </tr>
                  ))}
                </tbody>
                {items.length > 1 && (
                  <tfoot>
                    <tr className="border-t border-[var(--color-border)] font-semibold">
                      <td className="py-1.5" colSpan={2}>Total</td>
                      <td className="text-right">{Math.round(totals.cal)}</td>
                      <td className="text-right">{Math.round(totals.pro)}g</td>
                      <td className="text-right">{Math.round(totals.fat)}g</td>
                      <td className="text-right">{Math.round(totals.carb)}g</td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </>
          );
        })()}
      </div>

      {!resolved && (
        <div className="flex border-t border-[var(--color-border)]">
          <button
            onClick={handleReject}
            disabled={loading}
            className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-sm font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors disabled:opacity-50"
          >
            <X size={14} /> Dismiss
          </button>
          <div className="w-px bg-[var(--color-border)]" />
          <button
            onClick={handleConfirm}
            disabled={loading}
            className="flex-1 flex items-center justify-center gap-1.5 py-2.5 text-sm font-medium text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/20 transition-colors disabled:opacity-50"
          >
            <Check size={14} /> Confirm
          </button>
        </div>
      )}
    </motion.div>
  );
}
