import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { getAllExercises, createExercise, updateExercise, deleteExercise } from '../api/exercises';
import { Plus, Edit3, Trash2, Check, X } from 'lucide-react';

const MUSCLE_GROUPS = ['chest', 'back', 'legs', 'shoulders', 'arms', 'core', 'full_body'];
const EQUIPMENT = ['barbell', 'dumbbell', 'cable', 'machine', 'bodyweight', 'kettlebell', 'other'];

export default function AdminExercises() {
  const [exercises, setExercises] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [newName, setNewName] = useState('');
  const [newMg, setNewMg] = useState('chest');
  const [newEq, setNewEq] = useState('barbell');
  const [editId, setEditId] = useState<number | null>(null);
  const [editData, setEditData] = useState<any>({});

  const load = () => getAllExercises().then((r) => setExercises(r.data));
  useEffect(() => { load(); }, []);

  const filtered = exercises.filter((e) => e.name.toLowerCase().includes(search.toLowerCase()));

  const handleCreate = async () => {
    if (!newName.trim()) { toast.error('Name required'); return; }
    try {
      await createExercise({ name: newName, muscle_group: newMg, equipment: newEq });
      toast.success('Created!'); setNewName(''); load();
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Error'); }
  };

  const handleUpdate = async (id: number) => {
    try {
      await updateExercise(id, editData);
      toast.success('Updated!'); setEditId(null); load();
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Error'); }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteExercise(id);
      toast.success('Deleted!'); load();
    } catch (err: any) { toast.error(err.response?.data?.detail || 'Error'); }
  };

  const handleToggle = async (ex: any) => {
    await updateExercise(ex.id, { is_active: !ex.is_active });
    toast.success(ex.is_active ? 'Deactivated' : 'Activated'); load();
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Exercise Catalog (Admin)</h1>

      <div className="rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 sm:p-6 mb-6">
        <h2 className="text-lg font-semibold mb-3">Add New Exercise</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <input placeholder="Name" value={newName} onChange={(e) => setNewName(e.target.value)}
                 className="px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm" />
          <select value={newMg} onChange={(e) => setNewMg(e.target.value)}
                  className="px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm">
            {MUSCLE_GROUPS.map((m) => <option key={m}>{m}</option>)}
          </select>
          <select value={newEq} onChange={(e) => setNewEq(e.target.value)}
                  className="px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm">
            {EQUIPMENT.map((e) => <option key={e}>{e}</option>)}
          </select>
          <button onClick={handleCreate}
                  className="flex items-center justify-center gap-1 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold">
            <Plus size={16} /> Add
          </button>
        </div>
      </div>

      <div className="rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-4 sm:p-6">
        <input placeholder="Search exercises..." value={search} onChange={(e) => setSearch(e.target.value)}
               className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm mb-4" />

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-[var(--color-text-muted)]">
              <th className="pb-2">Name</th><th className="pb-2">Muscle</th><th className="pb-2">Equipment</th><th className="pb-2">Active</th><th className="pb-2 text-right">Actions</th>
            </tr></thead>
            <tbody>
              <AnimatePresence>
                {filtered.map((ex) => (
                  <motion.tr key={ex.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                             className="border-t border-[var(--color-border)]">
                    {editId === ex.id ? (
                      <>
                        <td className="py-2"><input value={editData.name ?? ex.name} onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                                                     className="px-2 py-1 rounded border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm w-full" /></td>
                        <td><select value={editData.muscle_group ?? ex.muscle_group} onChange={(e) => setEditData({ ...editData, muscle_group: e.target.value })}
                                    className="px-2 py-1 rounded border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm">
                          {MUSCLE_GROUPS.map((m) => <option key={m}>{m}</option>)}</select></td>
                        <td><select value={editData.equipment ?? ex.equipment} onChange={(e) => setEditData({ ...editData, equipment: e.target.value })}
                                    className="px-2 py-1 rounded border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm">
                          {EQUIPMENT.map((e) => <option key={e}>{e}</option>)}</select></td>
                        <td>-</td>
                        <td className="text-right space-x-1">
                          <button onClick={() => handleUpdate(ex.id)} className="text-green-500 hover:text-green-700"><Check size={16} /></button>
                          <button onClick={() => setEditId(null)} className="text-[var(--color-text-muted)]"><X size={16} /></button>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="py-2 font-medium">{ex.name}</td>
                        <td>{ex.muscle_group}</td>
                        <td>{ex.equipment}</td>
                        <td>
                          <button onClick={() => handleToggle(ex)}
                                  className={`px-2 py-0.5 rounded-full text-xs font-semibold ${ex.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                            {ex.is_active ? 'Yes' : 'No'}
                          </button>
                        </td>
                        <td className="text-right space-x-1">
                          <button onClick={() => { setEditId(ex.id); setEditData({}); }} className="text-indigo-500 hover:text-indigo-700"><Edit3 size={16} /></button>
                          <button onClick={() => handleDelete(ex.id)} className="text-red-400 hover:text-red-600"><Trash2 size={16} /></button>
                        </td>
                      </>
                    )}
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
