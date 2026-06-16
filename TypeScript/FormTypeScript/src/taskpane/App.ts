import { authContext } from '../auth/AuthContext';
import { renderLoginScreen } from '../auth/LoginScreen';
import { renderMainScreen } from '../components/MainScreen';
import { ModuleRegistry } from '../registry/ModuleRegistry';

let currentCleanup: (() => void) | null = null;

function cleanup() {
  if (currentCleanup) {
    currentCleanup();
    currentCleanup = null;
  }
}

export function renderApp() {
  cleanup();

  const root = document.getElementById('root');
  if (!root) return;

  root.innerHTML = '';

  const user = authContext.user;

  if (!user) {
    currentCleanup = renderLoginScreen(root);
  } else {
    currentCleanup = renderMainScreen(root, user, {
      onOpenModule(chave) {
        const mod = ModuleRegistry.getModulo(chave);
        if (!mod) return;

        cleanup();
        root.innerHTML = '';

        if (mod.renderizar) {
          currentCleanup = mod.renderizar(root, {
            onVoltar() {
              renderApp();
            },
          });
        }
      },
    });
  }
}
