SELECT
 * 
 FROM status_conta 
 WHERE dt_periodo_final >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) 
 AND dt_periodo_final <= CURDATE()
 AND ds_etapa <> 'Contas Canceladas'
 AND cd_estabelecimento NOT IN (264,265)
