import React, { useState } from 'react';
import { useAuth, UserInfo } from './AuthContext';
import { validateLogin } from './LoginService';
import { getPermissoes } from './PermissaoService';
import './LoginScreen.css';

export function LoginScreen() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await validateLogin(email, password);
      if (!user) {
        setError('Email ou senha inválidos');
        return;
      }

      const permissoes = await getPermissoes(user.UserID);

      const userInfo: UserInfo = {
        userId: user.UserID,
        email: user.Email,
        nome: user.Nome,
        permissoes,
      };

      login(userInfo);
    } catch (err) {
      setError('Erro ao conectar. Verifique se o Excel está aberto.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>FormLogin</h1>
          <p>Informe seus dados para acessar</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu@email.com"
              required
              autoFocus
            />
          </div>

          <div className="field">
            <label htmlFor="password">Senha</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Sua senha"
              required
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="btn-login" disabled={loading}>
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  );
}
