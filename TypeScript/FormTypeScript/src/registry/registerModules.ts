import { ModuleRegistry } from './ModuleRegistry';
import { renderCadastroForm } from '../components/CadastroForm';

export function registerAllModules() {
  ModuleRegistry.registrar({
    chave: 'CadastroForm',
    nome: 'Cadastro de Usuário',
    renderizar: renderCadastroForm,
  });
}
