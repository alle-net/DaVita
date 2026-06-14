import config from '../config.json';

export interface DataSourceConfig {
  type: 'local' | 'sharepoint';
  workbookUrl: string;
  sheetNames: {
    usuarios: string;
    permissoes: string;
    modulos: string;
  };
}

export interface AppConfig {
  dataSource: DataSourceConfig;
}

class ConfigService {
  private config: AppConfig;

  constructor() {
    this.config = config as AppConfig;
  }

  getConfig(): AppConfig {
    return this.config;
  }

  getSheetNames() {
    return this.config.dataSource.sheetNames;
  }

  getWorkbookUrl() {
    return this.config.dataSource.workbookUrl;
  }

  getDataSourceType() {
    return this.config.dataSource.type;
  }
}

export const configService = new ConfigService();
