import React from 'react';
import { useAuth } from '../auth/AuthContext';
import { ModuleRegistry } from '../registry/ModuleRegistry';
import './MainScreen.css';

export function MainScreen() {
  const { user, logout } = useAuth();

  const modulosPermitidos = ModuleRegistry.getModulosPermitidos(
    user?.permissoes ?? []
  );

  return (
    <div className="main-container">
      <div className="main-header">
        <div>
          <h1>Bem-vindo, {user?.nome ?? 'Usuário'}</h1>
          <p className="user-email">{user?.email}</p>
        </div>
        <button className="btn-logout" onClick={logout}>
          Sair
        </button>
      </div>

      <div className="modules-grid">
        {modulosPermitidos.length === 0 ? (
          <p className="no-modules">
            Você não tem acesso a nenhum módulo.
          </p>
        ) : (
          modulosPermitidos.map((mod) => (
            <div key={mod.chave} className="module-card">
              <h3>{mod.nome}</h3>
              <p>{mod.chave}</p>
              <button
                className="btn-open"
                onClick={() => mod.onOpen?.()}
              >
                Abrir
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
