import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { getGoals, updateGoals } from '../api/goals';

const GOAL_TYPES = ['muscle_gain', 'fat_loss', 'recomposition'];

export default function Settings() {
  const [goalType, setGoalType] = useState('fat_loss');
  const [cal, setCal] = useState(2000);
  const [prot, setProt] = useState(120);
  const [carb, setCarb] = useState(0);
  const [fat, setFat] = useState(0);
  const [tDays, setTDays] = useState(4);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getGoals().then((r) => {
      const g = r.data;
      setGoalType(g.goal_type || 'fat_loss');
      setCal(g.calorie_target || 2000);
      setProt(g.protein_target || 120);
      setCarb(g.carb_target || 0);
      setFat(g.fat_target || 0);
      setTDays(g.training_days_per_week || 4);
    });
  }, []);

  const handleSave = async () => {
    await updateGoals({ goal_type: goalType, calorie_target: cal, protein_target: prot, carb_target: carb, fat_target: fat, training_days_per_week: tDays });
    toast.success('Goals saved!');
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const inputClass = "w-full px-3 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50";

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="text-2xl font-bold mb-6">Goals & Settings</h1>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                  className="rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 sm:p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Goal Type</label>
          <select value={goalType} onChange={(e) => setGoalType(e.target.value)} className={inputClass}>
            {GOAL_TYPES.map((g) => <option key={g} value={g}>{g.replace('_', ' ')}</option>)}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Daily Calories (kcal)</label>
            <input type="number" value={cal} onChange={(e) => setCal(+e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Protein (g)</label>
            <input type="number" value={prot} onChange={(e) => setProt(+e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Carbs (g)</label>
            <input type="number" value={carb} onChange={(e) => setCarb(+e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Fat (g)</label>
            <input type="number" value={fat} onChange={(e) => setFat(+e.target.value)} className={inputClass} />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Training Days / Week</label>
          <input type="number" value={tDays} min={1} max={7} onChange={(e) => setTDays(+e.target.value)} className={inputClass} />
        </div>

        <motion.button
          onClick={handleSave} whileTap={{ scale: 0.97 }}
          className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold transition-colors"
        >
          {saved ? 'Saved!' : 'Save Goals'}
        </motion.button>
      </motion.div>
    </div>
  );
}
