import React from 'react';
import { LoginScreen } from '../auth/LoginScreen';
import { MainScreen } from '../components/MainScreen';
import { useAuth } from '../auth/AuthContext';

export function App() {
  const { user } = useAuth();

  return (
    <div className="app">
      {user ? <MainScreen /> : <LoginScreen />}
    </div>
  );
}
