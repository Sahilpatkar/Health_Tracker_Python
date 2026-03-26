import { createContext, useContext } from 'react';

export interface AuthUser {
  username: string;
  role: string;
}

export interface AuthCtx {
  user: AuthUser | null;
  token: string | null;
  login: (token: string, user: AuthUser) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthCtx>({
  user: null, token: null,
  login: () => {}, logout: () => {},
});

export const useAuth = () => useContext(AuthContext);
