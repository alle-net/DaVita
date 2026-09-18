SELECT *
FROM status_conta
WHERE dt_periodo_inicial >= :data_inicio
  AND dt_periodo_inicial <= :data_fim
  AND ds_etapa <> 'Contas Canceladas'
  AND cd_estabelecimento NOT IN (264,265)
