import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import DashboardCard from '../components/DashboardCard';
import { saveBodyMetrics, getBodyMetrics, uploadPhoto, getPhotos, deletePhoto } from '../api/body';
import { Camera, X, Trash2 } from 'lucide-react';

export default function BodyProgress() {
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [weight, setWeight] = useState(0);
  const [waist, setWaist] = useState(0);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [photos, setPhotos] = useState<any[]>([]);
  const [lightbox, setLightbox] = useState<string | null>(null);

  const load = () => {
    getBodyMetrics().then((r) => setMetrics(r.data));
    getPhotos().then((r) => setPhotos(r.data));
  };
  useEffect(load, []);

  const handleSaveMetrics = async () => {
    if (weight <= 0) { toast.error('Enter valid weight'); return; }
    await saveBodyMetrics({ date, weight_kg: weight, waist_cm: waist > 0 ? waist : undefined });
    toast.success('Saved!'); load();
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file, file.name || 'photo.jpg');
    fd.append('taken_date', date);
    fd.append('notes', '');
    const tid = toast.loading('Uploading…');
    try {
      await uploadPhoto(fd);
      toast.success('Photo uploaded!', { id: tid });
      load();
    } catch (err: unknown) {
      const ax = err as { response?: { status?: number; data?: { detail?: string } } };
      const msg =
        ax.response?.status === 413
          ? 'Photo is too large for the server. Try a smaller image.'
          : ax.response?.data?.detail || 'Upload failed. Check your connection and try again.';
      toast.error(msg, { id: tid });
    } finally {
      e.target.value = '';
    }
  };

  const handleDeletePhoto = async (id: number, filePath: string) => {
    if (!window.confirm('Delete this photo? This cannot be undone.')) return;
    try {
      await deletePhoto(id);
      toast.success('Photo deleted');
      if (lightbox === filePath) setLightbox(null);
      load();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      toast.error(ax.response?.data?.detail || 'Could not delete photo');
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Body Progress</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <DashboardCard title="Log Weight / Waist" delay={0}>
          <div className="space-y-3">
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
                   className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm" />
            <input type="number" placeholder="Body weight (kg)" value={weight || ''} onChange={(e) => setWeight(+e.target.value)} step="0.1"
                   className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm" />
            <input type="number" placeholder="Waist (cm) - optional" value={waist || ''} onChange={(e) => setWaist(+e.target.value)} step="0.5"
                   className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-dim)] text-sm" />
            <button onClick={handleSaveMetrics}
                    className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors">
              Save Metrics
            </button>
          </div>
        </DashboardCard>

        <DashboardCard title="Upload Photo" delay={0.1}>
          <div className="flex flex-col items-center gap-4">
            <Camera size={48} className="text-[var(--color-text-muted)]" />
            <label
              htmlFor="body-photo-upload"
              className="cursor-pointer px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm transition-colors"
            >
              Choose or take photo
            </label>
            <input
              id="body-photo-upload"
              type="file"
              accept="image/*"
              className="sr-only"
              onChange={handleUpload}
            />
          </div>
        </DashboardCard>
      </div>

      {metrics.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <DashboardCard title="Weight Trend" delay={0.2}>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis domain={['auto', 'auto']} />
                <Tooltip />
                <Line type="monotone" dataKey="weight_kg" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </DashboardCard>

          {metrics.some((m) => m.waist_cm) && (
            <DashboardCard title="Waist Trend" delay={0.3}>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={metrics.filter((m) => m.waist_cm)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis domain={['auto', 'auto']} />
                  <Tooltip />
                  <Line type="monotone" dataKey="waist_cm" stroke="#f59e0b" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </DashboardCard>
          )}
        </div>
      )}

      {photos.length > 0 && (
        <DashboardCard title="Photos" delay={0.4}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {photos.map((p: any) => (
              <motion.div
                key={p.id}
                whileHover={{ scale: 1.03 }}
                className="relative cursor-pointer group"
                onClick={() => setLightbox(p.file_path)}
              >
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    void handleDeletePhoto(p.id, p.file_path);
                  }}
                  className="absolute top-2 right-2 z-10 p-1.5 rounded-lg bg-black/60 text-white md:opacity-0 md:group-hover:opacity-100 hover:bg-red-600 focus:opacity-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-white transition-opacity"
                  aria-label="Delete photo"
                >
                  <Trash2 size={16} />
                </button>
                <img src={p.file_path} alt={p.notes || p.taken_date}
                     className="rounded-xl w-full h-40 object-cover border border-[var(--color-border)]" />
                <p className="text-xs text-[var(--color-text-muted)] mt-1 text-center">{p.taken_date}</p>
              </motion.div>
            ))}
          </div>
        </DashboardCard>
      )}

      <AnimatePresence>
        {lightbox && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
                      onClick={() => setLightbox(null)}>
            <button className="absolute top-4 right-4 text-white"><X size={32} /></button>
            <motion.img src={lightbox} initial={{ scale: 0.8 }} animate={{ scale: 1 }} exit={{ scale: 0.8 }}
                        className="max-w-full max-h-[85vh] rounded-2xl" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
