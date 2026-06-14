import React from 'react';
import { createRoot } from 'react-dom/client';
import { AuthProvider } from '../auth/AuthContext';
import { App } from './App';
import './taskpane.css';

Office.onReady(() => {
  const root = createRoot(document.getElementById('root')!);
  root.render(
    <AuthProvider>
      <App />
    </AuthProvider>
  );
});
