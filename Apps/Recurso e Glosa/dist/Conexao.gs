function getSheet(name) {
  Logger.log('getSheet - abrindo: ' + name);
  var ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  var sheet = ss.getSheetByName(name);
  if (!sheet) Logger.log('getSheet - ABA NAO ENCONTRADA: ' + name);
  return sheet;
}

function getSheetData(sheetName) {
  Logger.log('getSheetData - lendo: ' + sheetName);
  var sheet = getSheet(sheetName);
  if (!sheet) return null;
  var lastRow = sheet.getLastRow();
  Logger.log('getSheetData - lastRow: ' + lastRow);
  if (lastRow === 0) return null;
  var data = sheet.getRange(1, 1, lastRow, sheet.getLastColumn()).getValues();
  Logger.log('getSheetData - linhas: ' + data.length + ', colunas: ' + data[0].length);
  return data;
}

var _cache = CacheService.getScriptCache();
var CACHE_TTL = 300;
var CACHE_DADOS_TTL = 30;
var CACHE_USER_TTL = 300;

function getCachedData(sheetName) {
  var cacheKey = 'sheet_' + sheetName;
  var cached = _cache.get(cacheKey);
  if (cached) {
    Logger.log('getCachedData - cache hit: ' + sheetName);
    return JSON.parse(cached);
  }
  
  Logger.log('getCachedData - cache miss, lendo: ' + sheetName);
  var data = getSheetData(sheetName);
  if (data) {
    Logger.log('getCachedData - linhas lidas: ' + data.length + ', cacheando: ' + sheetName);
    _cache.put(cacheKey, JSON.stringify(data), CACHE_TTL);
  }
  return data;
}

function invalidateCache() {
  var keys = [
    'sheet_' + CONFIG.SHEETS.REGIONAIS,
    'sheet_' + CONFIG.SHEETS.UNIDADES,
    'sheet_' + CONFIG.SHEETS.HOSPITAIS,
    'sheet_' + CONFIG.SHEETS.STATUS_NFE,
    'sheet_' + CONFIG.SHEETS.MOTIVOS_GLOSA
  ];
  for (var i = 0; i < keys.length; i++) {
    _cache.remove(keys[i]);
  }
}

function invalidateAllCache() {
  var keys = [
    'sheet_' + CONFIG.SHEETS.REGIONAIS,
    'sheet_' + CONFIG.SHEETS.UNIDADES,
    'sheet_' + CONFIG.SHEETS.HOSPITAIS,
    'sheet_' + CONFIG.SHEETS.STATUS_NFE,
    'sheet_' + CONFIG.SHEETS.MOTIVOS_GLOSA,
    'sheet_' + CONFIG.SHEETS.DADOS
  ];
  for (var i = 0; i < keys.length; i++) {
    _cache.remove(keys[i]);
  }
  _lookupCache = {};
}

function invalidateCacheUsuario(userId) {
  _cache.remove('user_valid_' + userId);
}

function _colIndex(headers, names) {
  for (var i = 0; i < headers.length; i++) {
    var h = String(headers[i]).trim().toLowerCase();
    for (var j = 0; j < names.length; j++) {
      if (h === names[j]) return i;
    }
  }
  return -1;
}

var _lookupCache = {};

function getIdPorNome(sheetName, nome) {
  var cacheKey = sheetName + '::idPorNome';
  if (!_lookupCache[cacheKey]) {
    var data = getCachedData(sheetName);
    var map = {};
    if (data && data.length > 1) {
      var headers = data[0];
      var idCol = _colIndex(headers, ['id', 'idusuario', 'id usuario']);
      if (idCol < 0) idCol = 0;
      var nomeCol = _colIndex(headers, ['nome', 'nomeusuario', 'nome usuario', 'regional', 'unidade', 'hospital', 'motivo', 'motivoglosa', 'statusnfe']);
      if (nomeCol < 0) nomeCol = 1;
      var statusCol = _colIndex(headers, ['status', 'ativo']);
      for (var i = 1; i < data.length; i++) {
        if (statusCol >= 0 && String(data[i][statusCol]).trim() !== '1') continue;
        var id = String(data[i][idCol]).trim();
        var nm = String(data[i][nomeCol]).trim();
        if (nm) map[nm] = id;
      }
    }
    _lookupCache[cacheKey] = map;
  }
  return _lookupCache[cacheKey][String(nome).trim()] || null;
}

function getNomesDaAba(sheetName) {
  var cacheKey = sheetName + '::nomes';
  if (_lookupCache[cacheKey]) return _lookupCache[cacheKey];
  
  var data = getCachedData(sheetName);
  var nomes = [];
  if (data && data.length > 1) {
    var headers = data[0];
    var nomeCol = _colIndex(headers, ['nome', 'nomeusuario', 'nome usuario', 'regional', 'unidade', 'hospital', 'motivo', 'motivoglosa', 'statusnfe']);
    if (nomeCol < 0) nomeCol = 1;
    var statusCol = _colIndex(headers, ['status', 'ativo']);
    for (var i = 1; i < data.length; i++) {
      if (statusCol >= 0 && String(data[i][statusCol]).trim() !== '1') continue;
      var nome = String(data[i][nomeCol]).trim();
      if (nome) nomes.push(nome);
    }
  }
  _lookupCache[cacheKey] = nomes;
  return nomes;
}

function getIdsENomesDaAba(sheetName) {
  var data = getCachedData(sheetName);
  var result = { nomes: [], mapa: {} };
  if (data && data.length > 1) {
    var headers = data[0];
    var idCol = _colIndex(headers, ['id', 'idusuario', 'id usuario']);
    if (idCol < 0) idCol = 0;
    var nomeCol = _colIndex(headers, ['nome', 'nomeusuario', 'nome usuario', 'regional', 'unidade', 'hospital', 'motivo', 'motivoglosa', 'statusnfe']);
    if (nomeCol < 0) nomeCol = 1;
    for (var i = 1; i < data.length; i++) {
      var id = String(data[i][idCol]).trim();
      var nome = String(data[i][nomeCol]).trim();
      if (nome) {
        result.nomes.push(nome);
        result.mapa[id] = nome;
      }
    }
  }
  return result;
}

function getAllListas() {
  Logger.log('getAllListas - inicio');
  var result = {
    regionais: getNomesDaAba(CONFIG.SHEETS.REGIONAIS),
    unidades: getNomesDaAba(CONFIG.SHEETS.UNIDADES),
    hospitais: getNomesDaAba(CONFIG.SHEETS.HOSPITAIS),
    statusList: getNomesDaAba(CONFIG.SHEETS.STATUS_NFE),
    motivos: getNomesDaAba(CONFIG.SHEETS.MOTIVOS_GLOSA)
  };
  Logger.log('getAllListas - fim, regionais: ' + result.regionais.length + ', unidades: ' + result.unidades.length);
  return result;
}

function getMapaListas() {
  var regionalData = getIdsENomesDaAba(CONFIG.SHEETS.REGIONAIS);
  var unidadeData = getIdsENomesDaAba(CONFIG.SHEETS.UNIDADES);
  var hospitalData = getIdsENomesDaAba(CONFIG.SHEETS.HOSPITAIS);
  var statusData = getIdsENomesDaAba(CONFIG.SHEETS.STATUS_NFE);
  var motivoData = getIdsENomesDaAba(CONFIG.SHEETS.MOTIVOS_GLOSA);
  
  return {
    regionais: getNomesDaAba(CONFIG.SHEETS.REGIONAIS),
    unidades: getNomesDaAba(CONFIG.SHEETS.UNIDADES),
    hospitais: getNomesDaAba(CONFIG.SHEETS.HOSPITAIS),
    statusList: getNomesDaAba(CONFIG.SHEETS.STATUS_NFE),
    motivos: getNomesDaAba(CONFIG.SHEETS.MOTIVOS_GLOSA),
    regionalMap: regionalData.mapa,
    unidadeMap: unidadeData.mapa,
    hospitalMap: hospitalData.mapa,
    statusMap: statusData.mapa,
    motivoMap: motivoData.mapa
  };
}

function sanitizarInput(valor) {
  if (valor === null || valor === undefined) return '';
  return String(valor)
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .trim();
}

function onEditTrigger(e) {
  try {
    if (!e || !e.source || !e.range) return;
    var sheetName = e.range.getSheet().getName();
    var abasMonitoradas = [
      CONFIG.SHEETS.REGIONAIS,
      CONFIG.SHEETS.UNIDADES,
      CONFIG.SHEETS.HOSPITAIS,
      CONFIG.SHEETS.STATUS_NFE,
      CONFIG.SHEETS.MOTIVOS_GLOSA,
      CONFIG.SHEETS.USUARIOS,
      CONFIG.SHEETS.DADOS
    ];
    if (abasMonitoradas.indexOf(sheetName) !== -1) {
      invalidateAllCache();
    }
  } catch (err) {
    Logger.log('Erro no onEditTrigger: ' + err.message);
  }
}
