import { authContext, UserInfo } from './AuthContext';
import { validateLogin } from './LoginService';
import { getPermissoes } from './PermissaoService';
import './LoginScreen.css';

export function renderLoginScreen(root: HTMLElement): () => void {
  root.innerHTML = `
    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <h1>FormLogin</h1>
          <p>Informe seus dados para acessar</p>
        </div>
        <form class="login-form" id="loginForm">
          <div class="field">
            <label for="email">Email</label>
            <input id="email" type="email" placeholder="seu@email.com" required autofocus />
          </div>
          <div class="field">
            <label for="password">Senha</label>
            <input id="password" type="password" placeholder="Sua senha" required />
          </div>
          <div id="loginError" class="error-message" style="display:none"></div>
          <button type="submit" class="btn-login" id="loginBtn">Entrar</button>
        </form>
      </div>
    </div>
  `;

  const form = document.getElementById('loginForm') as HTMLFormElement;
  const emailInput = document.getElementById('email') as HTMLInputElement;
  const passwordInput = document.getElementById('password') as HTMLInputElement;
  const errorDiv = document.getElementById('loginError') as HTMLElement;
  const loginBtn = document.getElementById('loginBtn') as HTMLButtonElement;

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    errorDiv.style.display = 'none';
    loginBtn.disabled = true;
    loginBtn.textContent = 'Entrando...';

    try {
      const user = await validateLogin(emailInput.value, passwordInput.value);
      if (!user) {
        errorDiv.textContent = 'Email ou senha inválidos';
        errorDiv.style.display = 'block';
        return;
      }

      const permissoes = await getPermissoes(user.UserID);

      const userInfo: UserInfo = {
        userId: user.UserID,
        email: user.Email,
        nome: user.Nome,
        permissoes,
      };

      authContext.login(userInfo);
    } catch (err) {
      errorDiv.textContent = 'Erro ao conectar. Verifique se o Excel está aberto.';
      errorDiv.style.display = 'block';
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = 'Entrar';
    }
  };

  form.addEventListener('submit', handleSubmit);

  return () => {
    form.removeEventListener('submit', handleSubmit);
  };
}
