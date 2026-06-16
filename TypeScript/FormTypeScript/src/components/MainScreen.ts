import { authContext, UserInfo } from '../auth/AuthContext';
import { ModuleRegistry } from '../registry/ModuleRegistry';
import './MainScreen.css';

export interface MainScreenCallbacks {
  onOpenModule: (chave: string) => void;
}

export function renderMainScreen(
  root: HTMLElement,
  user: UserInfo,
  callbacks: MainScreenCallbacks
): () => void {
  const modulosPermitidos = ModuleRegistry.getModulosPermitidos(user.permissoes);

  const modulesHtml = modulosPermitidos.length === 0
    ? '<p class="no-modules">Você não tem acesso a nenhum módulo.</p>'
    : modulosPermitidos.map(mod => `
        <div class="module-card">
          <h3>${mod.nome}</h3>
          <p>${mod.chave}</p>
          <button class="btn-open" data-chave="${mod.chave}">Abrir</button>
        </div>
      `).join('');

  root.innerHTML = `
    <div class="main-container">
      <div class="main-header">
        <div>
          <h1>Bem-vindo, ${user.nome}</h1>
          <p class="user-email">${user.email}</p>
        </div>
        <button class="btn-logout" id="btnLogout">Sair</button>
      </div>
      <div class="modules-grid">
        ${modulesHtml}
      </div>
    </div>
  `;

  const logoutBtn = document.getElementById('btnLogout');
  const openButtons = root.querySelectorAll('.btn-open');

  const onLogout = () => {
    authContext.logout();
  };

  logoutBtn?.addEventListener('click', onLogout);

  openButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const chave = (btn as HTMLElement).getAttribute('data-chave');
      if (chave) {
        const mod = ModuleRegistry.getModulo(chave);
        mod?.onOpen?.();
        callbacks.onOpenModule(chave);
      }
    });
  });

  return () => {
    logoutBtn?.removeEventListener('click', onLogout);
  };
}
