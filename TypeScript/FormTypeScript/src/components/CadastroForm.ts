import { ModuloProps } from '../registry/ModuleRegistry';
import './CadastroForm.css';

interface FormData {
  nome: string;
  email: string;
  telefone: string;
  departamento: string;
}

export function renderCadastroForm(container: HTMLElement, props: ModuloProps): () => void {
  container.innerHTML = `
    <div class="cadastro-container">
      <div class="cadastro-header">
        <button class="btn-voltar" id="btnVoltar">&larr; Voltar</button>
        <h2>Cadastro de Usuário</h2>
      </div>
      <form class="cadastro-form" id="cadastroForm">
        <label class="cadastro-field">
          <span>Nome</span>
          <input type="text" id="campoNome" required />
        </label>
        <label class="cadastro-field">
          <span>Email</span>
          <input type="email" id="campoEmail" required />
        </label>
        <label class="cadastro-field">
          <span>Telefone</span>
          <input type="tel" id="campoTel" />
        </label>
        <label class="cadastro-field">
          <span>Departamento</span>
          <select id="campoDepto" required>
            <option value="">Selecione...</option>
            <option value="Administrativo">Administrativo</option>
            <option value="Financeiro">Financeiro</option>
            <option value="RH">RH</option>
            <option value="TI">TI</option>
            <option value="Operacional">Operacional</option>
          </select>
        </label>
        <button type="submit" class="btn-salvar">Salvar</button>
        <p id="cadastroSucesso" class="cadastro-sucesso" style="display:none">Cadastro salvo com sucesso!</p>
      </form>
    </div>
  `;

  const form = document.getElementById('cadastroForm') as HTMLFormElement;
  const sucesso = document.getElementById('cadastroSucesso') as HTMLElement;
  const nomeInput = document.getElementById('campoNome') as HTMLInputElement;
  const emailInput = document.getElementById('campoEmail') as HTMLInputElement;
  const telInput = document.getElementById('campoTel') as HTMLInputElement;
  const deptoSelect = document.getElementById('campoDepto') as HTMLSelectElement;

  const handleSubmit = (e: Event) => {
    e.preventDefault();
    const data: FormData = {
      nome: nomeInput.value,
      email: emailInput.value,
      telefone: telInput.value,
      departamento: deptoSelect.value,
    };
    console.log('Cadastro salvo:', data);
    sucesso.style.display = 'block';
    setTimeout(() => { sucesso.style.display = 'none'; }, 3000);
  };

  form.addEventListener('submit', handleSubmit);

  const voltarBtn = document.getElementById('btnVoltar');
  voltarBtn?.addEventListener('click', props.onVoltar);

  return () => {
    form.removeEventListener('submit', handleSubmit);
    voltarBtn?.removeEventListener('click', props.onVoltar);
  };
}
