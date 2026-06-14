import { configService } from '../config/ConfigService';

async function readSheetData(sheetName: string): Promise<(string | number)[][]> {
  return Excel.run(async (context) => {
    const sheet = context.workbook.worksheets.getItem(sheetName);
    const range = sheet.getUsedRange(true);
    range.load('values');
    await context.sync();
    return range.values as (string | number)[][];
  });
}

export async function getPermissoes(userId: number): Promise<string[]> {
  try {
    const sheetName = configService.getSheetNames().permissoes;
    const data = await readSheetData(sheetName);

    if (!data || data.length < 2) return [];

    const header = data[0].map(String);
    const uidIdx = header.findIndex((h) => h.trim().toLowerCase() === 'userid');
    const modIdx = header.findIndex((h) => h.trim().toLowerCase() === 'modulo');

    if (uidIdx === -1 || modIdx === -1) return [];

    const userPerms: string[] = [];
    for (let i = 1; i < data.length; i++) {
      if (Number(data[i][uidIdx]) === userId) {
        userPerms.push(String(data[i][modIdx]).trim());
      }
    }

    return userPerms;
  } catch (error) {
    console.error('Erro ao buscar permissoes:', error);
    return [];
  }
}

export async function getModulos(): Promise<{ ID: number; Chave: string; Nome: string }[]> {
  try {
    const sheetName = configService.getSheetNames().modulos;
    const data = await readSheetData(sheetName);

    if (!data || data.length < 2) return [];

    const header = data[0].map(String);
    const chaveIdx = header.findIndex((h) => h.trim().toLowerCase() === 'chave');
    const nomeIdx = header.findIndex((h) => h.trim().toLowerCase() === 'nome');
    const idIdx = header.findIndex((h) => h.trim().toLowerCase() === 'id');

    if (chaveIdx === -1) return [];

    return data.slice(1).map((row) => ({
      ID: idIdx >= 0 ? Number(row[idIdx]) : 0,
      Chave: String(row[chaveIdx]).trim(),
      Nome: nomeIdx >= 0 ? String(row[nomeIdx]).trim() : String(row[chaveIdx]).trim(),
    }));
  } catch (error) {
    console.error('Erro ao buscar modulos:', error);
    return [];
  }
}
