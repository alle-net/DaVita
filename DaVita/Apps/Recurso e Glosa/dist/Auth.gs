function listarUsuariosAtivos() {
  var data = getSheetData(CONFIG.SHEETS.USUARIOS);
  if (!data || data.length < 2) return [];
  var headers = data[0];
  var nomeCol = -1, emailCol = -1, ativoCol = -1;
  for (var i = 0; i < headers.length; i++) {
    var h = String(headers[i]).trim().toLowerCase();
    if (h === 'nome' || h === 'nomeusuario' || h === 'nome usuario') nomeCol = i;
    if (h === 'email') emailCol = i;
    if (h === 'ativo') ativoCol = i;
  }
  var usuarios = [];
  for (var i = 1; i < data.length; i++) {
    var ativo = ativoCol >= 0 ? String(data[i][ativoCol]).trim().toUpperCase() : 'S';
    if (ativo === 'S' && data[i][emailCol]) {
      var nome = nomeCol >= 0 && data[i][nomeCol] ? String(data[i][nomeCol]).trim() : String(data[i][emailCol]).trim();
      var email = String(data[i][emailCol]).trim();
      usuarios.push({ nome: nome, email: email });
    }
  }
  return usuarios;
}

function listarEmails() {
  var usuarios = listarUsuariosAtivos();
  return usuarios.map(function(u) { return u.email; });
}

function listarRegionais() { return getNomesDaAba(CONFIG.SHEETS.REGIONAIS); }
function listarUnidades() { return getNomesDaAba(CONFIG.SHEETS.UNIDADES); }
function listarHospitais() { return getNomesDaAba(CONFIG.SHEETS.HOSPITAIS); }
function listarStatus() { return getNomesDaAba(CONFIG.SHEETS.STATUS_NFE); }
function listarMotivos() { return getNomesDaAba(CONFIG.SHEETS.MOTIVOS_GLOSA); }

function doLogin(email, senha) {
  try {
    Logger.log('doLogin - inicio, email: ' + email);
    email = String(email || '').trim().toLowerCase();
    
    var tentativasKey = 'login_attempts_' + email;
    var tentativas = parseInt(_cache.get(tentativasKey) || '0');
    if (tentativas >= 5) {
      var bloqueadoAte = _cache.get(tentativasKey + '_until');
      if (bloqueadoAte && Date.now() < parseInt(bloqueadoAte)) {
        return { success: false, message: 'Muitas tentativas. Tente novamente em 1 minuto.' };
      } else {
        _cache.remove(tentativasKey);
        _cache.remove(tentativasKey + '_until');
        tentativas = 0;
      }
    }
    
    Logger.log('doLogin - lendo aba Usuarios');
    var data = getSheetData(CONFIG.SHEETS.USUARIOS);
    if (!data || data.length < 2) {
      Logger.log('doLogin - aba Usuarios vazia');
      return { success: false, message: 'Usuarios nao encontrados' };
    }
    
    var headers = data[0];
    var idCol = -1, emailCol = -1, senhaCol = -1, ativoCol = -1;
    for (var i = 0; i < headers.length; i++) {
      var h = String(headers[i]).trim().toLowerCase();
      if (h === 'id' || h === 'idusuario' || h === 'id usuario') idCol = i;
      if (h === 'email') emailCol = i;
      if (h === 'senha') senhaCol = i;
      if (h === 'ativo') ativoCol = i;
    }
    Logger.log('doLogin - colunas: id=' + idCol + ', email=' + emailCol + ', senha=' + senhaCol + ', ativo=' + ativoCol);
    
    senha = String(senha || '').trim();
    for (var i = 1; i < data.length; i++) {
      var uAtivo = ativoCol >= 0 ? String(data[i][ativoCol]).trim().toUpperCase() : 'S';
      var uEmail = emailCol >= 0 ? String(data[i][emailCol]).trim().toLowerCase() : '';
      var uSenha = senhaCol >= 0 ? String(data[i][senhaCol]).trim() : '';
      var uId = idCol >= 0 ? String(data[i][idCol]).trim() : '';
      if (uAtivo === 'S' && uEmail === email && uSenha === senha) {
        Logger.log('doLogin - login sucesso, userId: ' + uId);
        _cache.remove(tentativasKey);
        _cache.remove(tentativasKey + '_until');
        return { success: true, userId: uId, email: uEmail };
      }
    }
    
    Logger.log('doLogin - credenciais invalidas');
    tentativas++;
    _cache.put(tentativasKey, String(tentativas), 60);
    if (tentativas >= 5) {
      _cache.put(tentativasKey + '_until', String(Date.now() + 60000), 60);
    }
    return { success: false, message: 'Email ou senha invalidos' };
  } catch (e) {
    Logger.log('doLogin - erro: ' + e.message);
    return { success: false, message: 'Erro: ' + e.message };
  }
}

function verificarUserId(userId) {
  try {
    if (!userId) return null;
    
    Logger.log('verificarUserId - buscando: ' + userId);
    
    var data = getSheetData(CONFIG.SHEETS.USUARIOS);
    if (!data || data.length < 2) {
      Logger.log('verificarUserId - aba Usuarios vazia ou nao encontrada');
      return null;
    }
    
    var headers = data[0];
    var idCol = -1;
    for (var i = 0; i < headers.length; i++) {
      var h = String(headers[i]).trim().toLowerCase();
      if (h === 'id' || h === 'idusuario' || h === 'id usuario') { idCol = i; break; }
    }
    if (idCol < 0) {
      Logger.log('verificarUserId - coluna id nao encontrada');
      return null;
    }
    
    var searchId = String(userId).trim();
    for (var i = 1; i < data.length; i++) {
      if (String(data[i][idCol]).trim() === searchId) {
        Logger.log('verificarUserId - encontrado na linha ' + (i+1));
        return searchId;
      }
    }
    Logger.log('verificarUserId - nao encontrado');
    return null;
  } catch (e) {
    Logger.log('verificarUserId - erro: ' + e.message);
    return null;
  }
}
