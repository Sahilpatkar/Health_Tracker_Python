import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { login as apiLogin, register as apiRegister } from '../api/auth';
import toast from 'react-hot-toast';

export default function Login() {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [shake, setShake] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isRegister && password !== confirm) {
      toast.error('Passwords do not match');
      setShake(true);
      setTimeout(() => setShake(false), 500);
      return;
    }
    setLoading(true);
    try {
      if (isRegister) {
        await apiRegister(username, password);
        toast.success('Registered! Please log in.');
        setIsRegister(false);
      } else {
        const { data } = await apiLogin(username, password);
        login(data.token, { username: data.username, role: data.role });
        toast.success(`Welcome, ${data.username}!`);
        navigate('/workout');
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Something went wrong');
      setShake(true);
      setTimeout(() => setShake(false), 500);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[var(--color-surface-dim)]">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1, x: shake ? [0, -10, 10, -10, 10, 0] : 0 }}
        transition={{ duration: shake ? 0.4 : 0.5, ease: 'easeOut' }}
        className="w-full max-w-md"
      >
        <div className="rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] p-8 shadow-lg">
          <h1 className="text-3xl font-bold text-center mb-2 bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">
            Health Tracker
          </h1>
          <p className="text-center text-[var(--color-text-muted)] mb-8">
            {isRegister ? 'Create your account' : 'Sign in to continue'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5">Username</label>
              <input
                type="text" value={username} onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-dim)] focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1.5">Password</label>
              <input
                type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-dim)] focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition"
                required
              />
            </div>
            {isRegister && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}>
                <label className="block text-sm font-medium mb-1.5">Confirm Password</label>
                <input
                  type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-dim)] focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition"
                  required
                />
              </motion.div>
            )}
            <button
              type="submit" disabled={loading}
              className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition-colors disabled:opacity-50"
            >
              {loading ? 'Please wait...' : isRegister ? 'Register' : 'Sign In'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-[var(--color-text-muted)]">
            {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button onClick={() => setIsRegister(!isRegister)} className="text-indigo-500 font-medium hover:underline">
              {isRegister ? 'Sign In' : 'Register'}
            </button>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
