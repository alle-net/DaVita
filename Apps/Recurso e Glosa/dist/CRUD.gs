function validarCompetencia(comp) {
  if (!comp) return true;
  var str = String(comp).trim();
  var ano, mes;
  if (str.indexOf('-') >= 0) {
    var partes = str.split('-');
    ano = parseInt(partes[0]);
    mes = parseInt(partes[1]);
  } else if (str.length === 7) {
    mes = parseInt(str.substring(0, 2));
    ano = parseInt(str.substring(5));
  } else {
    var meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
    var match = str.match(/^([A-Za-z]{3})\/(\d{4})$/);
    if (match) {
      mes = meses.indexOf(match[1].toLowerCase()) + 1;
      ano = parseInt(match[2]);
    } else {
      return true;
    }
  }
  if (!ano || !mes || mes < 1 || mes > 12) return true;
  var agora = new Date();
  var anoAtual = agora.getFullYear();
  var mesAtual = agora.getMonth() + 1;
  if (ano > anoAtual || (ano === anoAtual && mes > mesAtual)) {
    return false;
  }
  return true;
}

function inserirRegistro(dados, userId) {
  try {
    var validUserId = verificarUserId(userId);
    if (!validUserId) return { success: false, message: 'Usuario nao autorizado' };

    if (dados.competencia && !validarCompetencia(dados.competencia)) {
      return { success: false, message: 'Competencia nao pode ser maior que o mes atual' };
    }

    var fatVal = parseFloat(dados.Faturamento);
    if (isNaN(fatVal) || fatVal <= 0) {
      return { success: false, message: 'Valor Faturado deve ser maior que zero' };
    }

    if (dados.Data) {
      var dataErr = validarDataNaoFutura(dados.Data, 'Data NFe');
      if (dataErr) return { success: false, message: dataErr };
    }
    var envioErr = validarDataNaoFutura(dados.Envio, 'Envio Faturamento');
    if (envioErr) return { success: false, message: envioErr };

    var sheet = getSheet(CONFIG.SHEETS.DADOS);
    var headers = sheet.getDataRange().getValues()[0];
    var row = [];

    dados.id = Utilities.getUuid();
    dados.IdUsuario = validUserId;
    dados.Data = new Date();

    dados.IdRegional = getIdPorNome(CONFIG.SHEETS.REGIONAIS, dados.IdRegional) || dados.IdRegional;
    dados.IdUnidade = getIdPorNome(CONFIG.SHEETS.UNIDADES, dados.IdUnidade) || dados.IdUnidade;
    dados.IdHospital = getIdPorNome(CONFIG.SHEETS.HOSPITAIS, dados.IdHospital) || dados.IdHospital;
    dados.IdStatus = getIdPorNome(CONFIG.SHEETS.STATUS_NFE, dados.IdStatus) || dados.IdStatus;
    dados.IdMotivo = getIdPorNome(CONFIG.SHEETS.MOTIVOS_GLOSA, dados.IdMotivo) || dados.IdMotivo;

    for (var i = 0; i < headers.length; i++) {
      var h = String(headers[i]).trim();
      var hLower = h.toLowerCase();
      if (hLower === 'idusuario' || hLower === 'id usuario' || hLower === 'id_usuario') {
        row.push(validUserId);
      } else if (hLower === 'data') {
        row.push(dados.Data);
      } else if (dados[h] !== undefined && dados[h] !== null) {
        row.push(sanitizarInput(dados[h]));
      } else {
        row.push('');
      }
    }
    sheet.appendRow(row);
    invalidateAllCache();
    invalidateCacheUsuario(validUserId);
    return { success: true, message: 'Registro inserido com sucesso' };
  } catch (e) {
    return { success: false, message: 'Erro: ' + e.message };
  }
}

function validarDataNaoFutura(dataStr, nome) {
  if (!dataStr) return null;
  var data = new Date(dataStr + 'T00:00:00');
  var hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  if (data > hoje) return nome + ' nao pode ser maior que a data atual';
  return null;
}

function formatarCompetencia(comp) {
  if (!comp) return '';
  var str;
  if (comp instanceof Date) {
    var ano = comp.getFullYear();
    var mes = comp.getMonth() + 1;
    var meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    return meses[mes - 1] + '/' + ano;
  }
  str = String(comp).trim();
  var partes = str.split('-');
  if (partes.length >= 2) {
    var ano = partes[0];
    var mes = partes[1];
    var meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    var mesIdx = parseInt(mes) - 1;
    if (mesIdx >= 0 && mesIdx < 12) {
      return meses[mesIdx] + '/' + ano;
    }
  }
  if (str.length === 7) {
    var mes2 = parseInt(str.substring(0, 2)) - 1;
    var meses2 = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
    if (mes2 >= 0 && mes2 < 12) {
      return meses2[mes2] + '/' + str.substring(5);
    }
  }
  return str;
}

function enriquecerRegistro(r, listas) {
  var idR = String(r.IdRegional || '').trim();
  var idU = String(r.IdUnidade || '').trim();
  var idH = String(r.IdHospital || '').trim();
  var idS = String(r.IdStatus || '').trim();
  var idM = String(r.IdMotivo || '').trim();

  var dataStr = r.Data;
  if (dataStr instanceof Date) dataStr = dataStr.toISOString();
  else dataStr = String(dataStr || '').trim();

  var envioStr = r.Envio;
  if (envioStr instanceof Date) envioStr = envioStr.toISOString();
  else envioStr = String(envioStr || '').trim();

  return {
    id: String(r.id || '').trim(),
    IdUsuario: String(r.IdUsuario || '').trim(),
    competencia: formatarCompetencia(r.competencia),
    IdRegional: idR,
    IdUnidade: idU,
    IdHospital: idH,
    IdStatus: idS,
    IdMotivo: idM,
    Envio: envioStr,
    Faturamento: r.Faturamento,
    Perda: r.Perda,
    Glosa: r.Glosa,
    Observacao: String(r.Observacao || '').trim(),
    Data: dataStr,
    NFe: String(r.NFe || '').trim(),
    Titulo: String(r.Titulo || '').trim(),
    Regional: listas.regionalMap[idR] || idR,
    Unidade: listas.unidadeMap[idU] || idU,
    Hospital: listas.hospitalMap[idH] || idH,
    StatusNFe: listas.statusMap[idS] || idS,
    MotivoGlosa: listas.motivoMap[idM] || idM
  };
}

function listarRegistros(userId, page, pageSize, searchTerm) {
  try {
    var validUserId = verificarUserId(userId);
    if (!validUserId) return { dados: [], total: 0, page: 1, pageSize: 10, totalPages: 0 };

    var p = Math.max(1, parseInt(page) || 1);
    var ps = Math.max(10, Math.min(100, parseInt(pageSize) || 10));
    var search = searchTerm ? String(searchTerm).trim().toLowerCase() : '';
    
    var sheet = getSheet(CONFIG.SHEETS.DADOS);
    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { dados: [], total: 0, page: 1, pageSize: ps, totalPages: 0 };
    
    var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    
    var idUsuarioCol = -1;
    for (var i = 0; i < headers.length; i++) {
      var h = String(headers[i]).trim().toLowerCase();
      if (h === 'idusuario' || h === 'id usuario' || h === 'id_usuario') idUsuarioCol = i;
    }
    
    Logger.log('listarRegistros - userId: ' + validUserId + ', lastRow: ' + lastRow + ', idUsuarioCol: ' + idUsuarioCol + ', search: "' + search + '"');
    
    var allData = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
    Logger.log('listarRegistros - totalLinhasLidas: ' + allData.length);
    
    var listas = getMapaListas();
    var todosEnriquecidos = [];
    
    for (var i = 0; i < allData.length; i++) {
      var rowUserId = idUsuarioCol >= 0 ? String(allData[i][idUsuarioCol]).trim() : '';
      if (rowUserId === validUserId) {
        var row = {};
        for (var j = 0; j < headers.length; j++) {
          row[String(headers[j]).trim()] = allData[i][j];
        }
        todosEnriquecidos.push(enriquecerRegistro(row, listas));
      }
    }
    
    Logger.log('listarRegistros - registrosDoUsuario: ' + todosEnriquecidos.length);
    
    var filtrados = todosEnriquecidos;
    if (search) {
      filtrados = [];
      var colunasBusca = ['Titulo', 'competencia', 'Regional', 'Unidade', 'Hospital', 'NFe', 'Data', 'StatusNFe', 'MotivoGlosa', 'Envio', 'Faturamento', 'Glosa', 'Perda', 'Observacao', 'id', 'IdUsuario'];
      for (var i = 0; i < todosEnriquecidos.length; i++) {
        var r = todosEnriquecidos[i];
        var match = false;
        for (var j = 0; j < colunasBusca.length; j++) {
          var val = r[colunasBusca[j]];
          if (val !== undefined && val !== null && String(val).toLowerCase().indexOf(search) !== -1) {
            match = true;
            break;
          }
        }
        if (match) filtrados.push(r);
      }
      Logger.log('listarRegistros - apos filtro: ' + filtrados.length + ' (search: "' + search + '")');
    }
    
    filtrados.reverse();
    var total = filtrados.length;
    var totalPages = Math.ceil(total / ps);
    if (p > totalPages && totalPages > 0) p = totalPages;
    
    var sumFaturamento = 0, sumGlosa = 0, sumPerda = 0;
    for (var i = 0; i < filtrados.length; i++) {
      sumFaturamento += parseFloat(filtrados[i].Faturamento) || 0;
      sumGlosa += parseFloat(filtrados[i].Glosa) || 0;
      sumPerda += parseFloat(filtrados[i].Perda) || 0;
    }
    
    var start = (p - 1) * ps;
    var end = Math.min(start + ps, total);
    var paginados = filtrados.slice(start, end);
    
    Logger.log('listarRegistros - pagina: ' + p + ', retornando: ' + paginados.length + ' registros');
    
    return {
      dados: paginados,
      total: total,
      page: p,
      pageSize: ps,
      totalPages: totalPages,
      sumFaturamento: sumFaturamento,
      sumGlosa: sumGlosa,
      sumPerda: sumPerda
    };
  } catch (e) {
    Logger.log('Erro listarRegistros: ' + e.message);
    return { dados: [], total: 0, page: 1, pageSize: 10, totalPages: 0, error: e.message };
  }
}

function editarRegistro(id, dados, userId) {
  try {
    var validUserId = verificarUserId(userId);
    if (!validUserId) return { success: false, message: 'Usuario nao autorizado' };

    if (dados.competencia && !validarCompetencia(dados.competencia)) {
      return { success: false, message: 'Competencia nao pode ser maior que o mes atual' };
    }

    var fatVal = parseFloat(dados.Faturamento);
    if (isNaN(fatVal) || fatVal <= 0) {
      return { success: false, message: 'Valor Faturado deve ser maior que zero' };
    }

    var dataErr = validarDataNaoFutura(dados.Data, 'Data NFe');
    if (dataErr) return { success: false, message: dataErr };
    var envioErr = validarDataNaoFutura(dados.Envio, 'Envio Faturamento');
    if (envioErr) return { success: false, message: envioErr };

    var sheet = getSheet(CONFIG.SHEETS.DADOS);
    var range = sheet.getDataRange();
    var values = range.getValues();
    var headers = values[0];
    var idCol = -1, userCol = -1;
    for (var i = 0; i < headers.length; i++) {
      var h = String(headers[i]).trim().toLowerCase();
      if (h === 'id') idCol = i;
      if (h === 'idusuario' || h === 'id usuario' || h === 'id_usuario') userCol = i;
    }

    dados.IdRegional = getIdPorNome(CONFIG.SHEETS.REGIONAIS, dados.IdRegional) || dados.IdRegional;
    dados.IdUnidade = getIdPorNome(CONFIG.SHEETS.UNIDADES, dados.IdUnidade) || dados.IdUnidade;
    dados.IdHospital = getIdPorNome(CONFIG.SHEETS.HOSPITAIS, dados.IdHospital) || dados.IdHospital;
    dados.IdStatus = getIdPorNome(CONFIG.SHEETS.STATUS_NFE, dados.IdStatus) || dados.IdStatus;
    dados.IdMotivo = getIdPorNome(CONFIG.SHEETS.MOTIVOS_GLOSA, dados.IdMotivo) || dados.IdMotivo;

    var searchId = String(id).trim();
    for (var i = 1; i < values.length; i++) {
      var rowId = String(values[i][idCol]).trim();
      if (rowId === searchId) {
        if (userCol >= 0 && String(values[i][userCol]).trim() !== validUserId) {
          return { success: false, message: 'Sem permissao para editar este registro' };
        }
        var newRow = [];
        for (var j = 0; j < headers.length; j++) {
          var header = headers[j];
          if (dados[header] !== undefined) {
            newRow.push(sanitizarInput(dados[header]));
          } else {
            newRow.push(values[i][j]);
          }
        }
        sheet.getRange(i + 1, 1, 1, headers.length).setValues([newRow]);
        invalidateAllCache();
        invalidateCacheUsuario(validUserId);
        return { success: true, message: 'Registro atualizado com sucesso' };
      }
    }
    return { success: false, message: 'Registro nao encontrado' };
  } catch (e) {
    return { success: false, message: 'Erro: ' + e.message };
  }
}

function excluirRegistro(id, userId) {
  try {
    var validUserId = verificarUserId(userId);
    if (!validUserId) return { success: false, message: 'Usuario nao autorizado' };

    var sheet = getSheet(CONFIG.SHEETS.DADOS);
    var range = sheet.getDataRange();
    var values = range.getValues();
    var headers = values[0];
    var idCol = -1, userCol = -1;
    for (var i = 0; i < headers.length; i++) {
      var h = String(headers[i]).trim().toLowerCase();
      if (h === 'id') idCol = i;
      if (h === 'idusuario' || h === 'id usuario' || h === 'id_usuario') userCol = i;
    }

    var searchId = String(id).trim();
    Logger.log('excluirRegistro - buscando ID: "' + searchId + '" (tipo: ' + typeof id + ')');
    
    for (var i = 1; i < values.length; i++) {
      var rowId = String(values[i][idCol]).trim();
      Logger.log('excluirRegistro - comparando com row ' + (i+1) + ': "' + rowId + '"');
      if (rowId === searchId) {
        if (userCol >= 0 && String(values[i][userCol]).trim() !== validUserId) {
          return { success: false, message: 'Sem permissao para excluir este registro' };
        }
        sheet.deleteRow(i + 1);
        invalidateAllCache();
        invalidateCacheUsuario(validUserId);
        return { success: true, message: 'Registro excluido com sucesso' };
      }
    }
    Logger.log('excluirRegistro - ID nao encontrado. Total de linhas: ' + values.length);
    return { success: false, message: 'Registro nao encontrado' };
  } catch (e) {
    Logger.log('excluirRegistro - Erro: ' + e.message);
    return { success: false, message: 'Erro: ' + e.message };
  }
}

function carregarApp(userId, forceRefresh) {
  try {
    Logger.log('carregarApp - inicio, userId: ' + userId);
    var validUserId = verificarUserId(userId);
    if (!validUserId) return { error: 'Usuario nao autorizado' };
    Logger.log('carregarApp - userId validado: ' + validUserId);

    if (forceRefresh) {
      Logger.log('carregarApp - forceRefresh, invalidando cache');
      invalidateAllCache();
      invalidateCacheUsuario(validUserId);
    }

    Logger.log('carregarApp - chamando getMapaListas');
    var listas = getMapaListas();
    Logger.log('carregarApp - listas obtidas, regionais: ' + listas.regionais.length);
    
    return {
      total: -1,
      page: 0,
      pageSize: 50,
      totalPages: 0,
      regionais: listas.regionais,
      unidades: listas.unidades,
      hospitais: listas.hospitais,
      statusList: listas.statusList,
      motivos: listas.motivos,
      versao: getVersaoListas(),
      userId: validUserId
    };
  } catch (e) {
    Logger.log('Erro carregarApp: ' + e.message);
    return { error: 'Erro: ' + e.message };
  }
}

function getListas() {
  try {
    return getAllListas();
  } catch (e) {
    return { regionais: [], unidades: [], hospitais: [], statusList: [], motivos: [] };
  }
}

function testarListagem() {
  var sheet = getSheet(CONFIG.SHEETS.DADOS);
  Logger.log('Sheet: ' + sheet.getName());
  Logger.log('lastRow: ' + sheet.getLastRow());
  Logger.log('lastColumn: ' + sheet.getLastColumn());
  
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  Logger.log('Headers: ' + JSON.stringify(headers));
  
  var idUsuarioCol = -1;
  for (var i = 0; i < headers.length; i++) {
    var h = String(headers[i]).trim().toLowerCase();
    if (h === 'idusuario' || h === 'id usuario' || h === 'id_usuario') { idUsuarioCol = i; break; }
  }
  Logger.log('idUsuarioCol: ' + idUsuarioCol);
  
  var allData = sheet.getRange(2, 1, Math.min(sheet.getLastRow() - 1, 10), sheet.getLastColumn()).getValues();
  Logger.log('Linhas lidas (amostra 10): ' + allData.length);
  
  for (var i = 0; i < allData.length; i++) {
    Logger.log('Linha ' + (i+2) + ' - IdUsuario: "' + allData[i][idUsuarioCol] + '"');
  }
  
  Logger.log('TESTE CONCLUIDO');
}
