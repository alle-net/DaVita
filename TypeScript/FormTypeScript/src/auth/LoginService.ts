import { configService } from '../config/ConfigService';

export interface UsuarioRow {
  UserID: number;
  Email: string;
  Senha: string;
  Nome: string;
  Status: number;
}

async function readSheetData(sheetName: string): Promise<(string | number)[][]> {
  return Excel.run(async (context) => {
    const sheet = context.workbook.worksheets.getItem(sheetName);
    const range = sheet.getUsedRange(true);
    range.load('values');
    await context.sync();
    return range.values as (string | number)[][];
  });
}

function getHeaderRow(data: (string | number)[][]): string[] | null {
  if (!data || data.length === 0) return null;
  return data[0].map(String);
}

function findColumnIndex(header: string[], name: string): number {
  return header.findIndex((h) => h.trim().toLowerCase() === name.toLowerCase());
}

export async function validateLogin(
  email: string,
  password: string
): Promise<UsuarioRow | null> {
  try {
    const sheetName = configService.getSheetNames().usuarios;
    const data = await readSheetData(sheetName);

    if (!data || data.length < 2) return null;

    const header = getHeaderRow(data);
    if (!header) return null;

    const colEmail = findColumnIndex(header, 'Email');
    const colSenha = findColumnIndex(header, 'Senha');
    const colUserID = findColumnIndex(header, 'UserID');
    const colNome = findColumnIndex(header, 'Nome');
    const colStatus = findColumnIndex(header, 'Status');

    if (colEmail === -1 || colSenha === -1) return null;

    for (let i = 1; i < data.length; i++) {
      const row = data[i];
      const rowEmail = String(row[colEmail] ?? '').trim().toLowerCase();
      const rowSenha = String(row[colSenha] ?? '').trim();
      const rowStatus = colStatus >= 0 ? Number(row[colStatus] ?? 0) : 1;

      if (rowEmail === email.toLowerCase() && rowSenha === password && rowStatus === 1) {
        return {
          UserID: colUserID >= 0 ? Number(row[colUserID]) : i,
          Email: rowEmail,
          Senha: '',
          Nome: colNome >= 0 ? String(row[colNome] ?? '') : rowEmail,
          Status: 1,
        };
      }
    }

    return null;
  } catch (error) {
    console.error('Erro ao validar login:', error);
    return null;
  }
}
