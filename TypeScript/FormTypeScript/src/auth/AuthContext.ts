export interface UserInfo {
  userId: number;
  email: string;
  nome: string;
  permissoes: string[];
}

type AuthListener = (user: UserInfo | null) => void;

class AuthContextClass {
  private _user: UserInfo | null = null;
  private listeners: AuthListener[] = [];

  get user(): UserInfo | null {
    return this._user;
  }

  login(userInfo: UserInfo) {
    this._user = userInfo;
    this.notify();
  }

  logout() {
    this._user = null;
    this.notify();
  }

  subscribe(listener: AuthListener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notify() {
    this.listeners.forEach(l => l(this._user));
  }
}

export const authContext = new AuthContextClass();
