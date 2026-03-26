import { lazy, useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthContext } from './hooks/useAuth';
import type { AuthUser } from './hooks/useAuth';
import Layout from './components/Layout';
import Login from './pages/Login';

const WorkoutDashboard = lazy(() => import('./pages/WorkoutDashboard'));
const WorkoutLog = lazy(() => import('./pages/WorkoutLog'));
const NutritionDashboard = lazy(() => import('./pages/NutritionDashboard'));
const NutritionLog = lazy(() => import('./pages/NutritionLog'));
const ProgressDashboard = lazy(() => import('./pages/ProgressDashboard'));
const BodyProgress = lazy(() => import('./pages/BodyProgress'));
const Settings = lazy(() => import('./pages/Settings'));
const AdminExercises = lazy(() => import('./pages/AdminExercises'));
const AdminUsers = lazy(() => import('./pages/AdminUsers'));
const Chat = lazy(() => import('./pages/Chat'));

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token');
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const raw = localStorage.getItem('user');
  const user = raw ? JSON.parse(raw) : null;
  return user?.role === 'admin' ? <>{children}</> : <Navigate to="/workout" replace />;
}

export default function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem('token');
    const u = localStorage.getItem('user');
    if (t && u) { setToken(t); setUser(JSON.parse(u)); }
  }, []);

  const login = (t: string, u: AuthUser) => {
    localStorage.setItem('token', t);
    localStorage.setItem('user', JSON.stringify(u));
    setToken(t); setUser(u);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null); setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      <BrowserRouter>
        <Toaster position="top-right" toastOptions={{ duration: 3000, style: { borderRadius: '12px', padding: '12px 16px' } }} />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/workout" replace />} />
            <Route path="workout" element={<WorkoutDashboard />} />
            <Route path="workout/log" element={<WorkoutLog />} />
            <Route path="nutrition" element={<NutritionDashboard />} />
            <Route path="nutrition/log" element={<NutritionLog />} />
            <Route path="progress" element={<ProgressDashboard />} />
            <Route path="body" element={<BodyProgress />} />
            <Route path="settings" element={<Settings />} />
            <Route path="chat" element={<Chat />} />
            <Route path="admin/exercises" element={<AdminRoute><AdminExercises /></AdminRoute>} />
            <Route path="admin/users" element={<AdminRoute><AdminUsers /></AdminRoute>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  );
}
