import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export interface UserInfo {
  userId: number;
  email: string;
  nome: string;
  permissoes: string[];
}

interface AuthContextType {
  user: UserInfo | null;
  login: (userInfo: UserInfo) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  login: () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);

  const login = useCallback((userInfo: UserInfo) => {
    setUser(userInfo);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
