function doGet() {
  invalidateAllCache();
  return HtmlService.createTemplateFromFile('Index')
    .evaluate()
    .setTitle('Gestao de Recursos e Glosas')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

function getVersaoListas() {
  var abas = [
    CONFIG.SHEETS.REGIONAIS,
    CONFIG.SHEETS.UNIDADES,
    CONFIG.SHEETS.HOSPITAIS,
    CONFIG.SHEETS.STATUS_NFE,
    CONFIG.SHEETS.MOTIVOS_GLOSA,
    CONFIG.SHEETS.USUARIOS
  ];
  var hash = '';
  for (var i = 0; i < abas.length; i++) {
    var sheet = getSheet(abas[i]);
    if (sheet) {
      hash += sheet.getLastRow() + '-' + (sheet.getLastColumn() || 0) + '-';
    }
  }
  return hash;
}

function setupOnEditTrigger() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'onEditTrigger') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
  ScriptApp.newTrigger('onEditTrigger')
    .forSpreadsheet(ss)
    .onEdit()
    .create();
  return 'Trigger configurado com sucesso!';
}