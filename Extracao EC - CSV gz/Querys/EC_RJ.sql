SELECT
  cd_estabelecimento,
  ds_estabelecimento,
  cd_convenio,
  ds_convenio,
  cnpj_convenio,
  faturamento_convenio,
  cd_plano,
  ds_plano,
  ds_hospital,
  tipo_hospital,
  procedimento,
  nr_interno_conta,
  status_conta,
  vl_conta,
  dt_mesano_referencia,
  dt_periodo_inicial,
  dt_periodo_final,
  nr_atendimento,
  ds_etapa,
  usuario_etapa,
  ds_setor_atendimento_etapa,
  dt_etapa,
  obs_etapa,
  cd_paciente,
  nm_paciente,
  matricula_paciente,
  cpf_paciente,
  nr_guia,
  nr_titulo,
  dt_titulo,
  nota_fiscal,
  dt_emissao_nf,
  lote,
  protocolo,
  status_autorizacao
FROM status_conta
WHERE dt_periodo_final >= CURDATE() - INTERVAL (DAY(CURDATE()) - 1) DAY - INTERVAL 6 MONTH
  AND dt_periodo_final <= CURDATE()
  AND ds_etapa <> 'Contas Canceladas'
  AND cd_estabelecimento NOT IN (264,265)
  AND ds_estabelecimento IN (
    'DaVita Nephron Care Home Care',
    'DaVita Rien',
    'DaVita Rien Home Care',
    'DaVita Nephron Care (Regra Terceira)',
    'DaVita Campos',
    'DaVita Macae',
    'DaVita Tijuca',
    'DaVita São Cristovão'
  )
