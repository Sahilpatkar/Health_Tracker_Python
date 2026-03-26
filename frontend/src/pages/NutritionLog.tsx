import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { getFoodItems, addFoodIntake, addWater, getFoodIntake } from '../api/food';
import { Droplets } from 'lucide-react';

const MEAL_TYPES = ['Breakfast', 'Morning Snacks', 'Lunch', 'Evening Snacks', 'Dinner'];

export default function NutritionLog() {
  const [foodItems, setFoodItems] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mealType, setMealType] = useState('Lunch');
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [quantity, setQuantity] = useState(1);
  const [waterDate, setWaterDate] = useState(new Date().toISOString().slice(0, 10));
  const [waterAmount, setWaterAmount] = useState(0.5);
  const [recentIntake, setRecentIntake] = useState<any[]>([]);

  useEffect(() => {
    getFoodItems().then((r) => {
      setFoodItems(r.data);
      if (r.data.length) setSelectedId(r.data[0].id);
    });
    getFoodIntake(7).then((r) => setRecentIntake(r.data));
  }, []);

  const selectedItem = foodItems.find((f) => f.id === selectedId);

  const handleAddFood = async () => {
    if (!selectedItem || quantity <= 0) { toast.error('Select item & quantity'); return; }
    try {
      await addFoodIntake({
        food_id: selectedItem.id, date, meal_type: mealType,
        food_item: selectedItem.food_item, quantity, unit: selectedItem.serving_size,
      });
      toast.success(`Added ${selectedItem.food_item}`);
      getFoodIntake(7).then((r) => setRecentIntake(r.data));
    } catch { toast.error('Failed'); }
  };

  const handleAddWater = async () => {
    try {
      await addWater({ date: waterDate, water_intake: waterAmount });
      toast.success(`Logged ${waterAmount}L water`);
    } catch { toast.error('Failed'); }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Log Food & Water</h1>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                  className="rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 sm:p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Food Intake</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium mb-1 text-[var(--color-text-muted)]">Date</label>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
                   className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1 text-[var(--color-text-muted)]">Meal Type</label>
            <select value={mealType} onChange={(e) => setMealType(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm">
              {MEAL_TYPES.map((m) => <option key={m}>{m}</option>)}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium mb-1 text-[var(--color-text-muted)]">Food Item</label>
            <select value={selectedId ?? ''} onChange={(e) => setSelectedId(+e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm">
              {foodItems.map((f) => <option key={f.id} value={f.id}>{f.food_item}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium mb-1 text-[var(--color-text-muted)]">Quantity</label>
            <input type="number" value={quantity} onChange={(e) => setQuantity(+e.target.value)} step="0.1" min="0"
                   className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm" />
          </div>
        </div>
        {selectedItem && (
          <p className="text-xs text-[var(--color-text-muted)] mb-4">
            Serving: {selectedItem.serving_size} &middot; {selectedItem.calories} kcal &middot; {selectedItem.protein}g protein
          </p>
        )}
        <button onClick={handleAddFood}
                className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors">
          Add Food
        </button>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                  className="rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 sm:p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><Droplets size={20} className="text-blue-500" /> Water Intake</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium mb-1 text-[var(--color-text-muted)]">Date</label>
            <input type="date" value={waterDate} onChange={(e) => setWaterDate(e.target.value)}
                   className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm" />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1 text-[var(--color-text-muted)]">Litres</label>
            <input type="number" value={waterAmount} onChange={(e) => setWaterAmount(+e.target.value)} step="0.1" min="0"
                   className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm" />
          </div>
        </div>
        <button onClick={handleAddWater}
                className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm transition-colors">
          Log Water
        </button>
      </motion.div>

      {recentIntake.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
                    className="rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 sm:p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Entries (7 days)</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-[var(--color-text-muted)]">
                <th className="pb-2">Date</th><th className="pb-2">Meal</th><th className="pb-2">Item</th><th className="pb-2">Qty</th>
              </tr></thead>
              <tbody>
                {recentIntake.slice(0, 20).map((r: any, i: number) => (
                  <tr key={i} className="border-t border-[var(--color-border)]">
                    <td className="py-2">{r.date}</td><td>{r.meal_type}</td><td>{r.food_item}</td><td>{r.quantity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </div>
  );
}
