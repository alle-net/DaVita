export interface ModuloProps {
  onVoltar: () => void;
}

export type RenderModulo = (container: HTMLElement, props: ModuloProps) => (() => void);

export interface Modulo {
  chave: string;
  nome: string;
  renderizar?: RenderModulo;
  onOpen?: () => void;
}

class ModuleRegistryClass {
  private modulos = new Map<string, Modulo>();

  registrar(modulo: Modulo) {
    this.modulos.set(modulo.chave, modulo);
  }

  getModulo(chave: string): Modulo | undefined {
    return this.modulos.get(chave);
  }

  getModulosPermitidos(permissoes: string[]): Modulo[] {
    return permissoes
      .map((chave) => this.modulos.get(chave))
      .filter((m): m is Modulo => m !== undefined);
  }

  listarTodos(): Modulo[] {
    return Array.from(this.modulos.values());
  }
}

export const ModuleRegistry = new ModuleRegistryClass();
