import { registerAllModules } from '../registry/registerModules';
import { authContext } from '../auth/AuthContext';
import { renderApp } from './App';
import './taskpane.css';

registerAllModules();

authContext.subscribe(() => {
  renderApp();
});

Office.onReady(() => {
  renderApp();
});
