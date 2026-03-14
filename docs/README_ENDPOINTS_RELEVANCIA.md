# Endpoints e Relevancia para o Projeto

Esta documentacao responde duas perguntas de forma objetiva:

1. qual endpoint ou recurso cada módulo extrai;
2. por que esse dado existe no projeto.

O objetivo deste arquivo e evitar que a relevancia de cada fonte fique
"subentendida" no codigo.

## Como ler esta documentacao

Cada item abaixo informa:

- o endpoint ou recurso extraido;
- o papel dele no projeto;
- o que ele agrega na analise;
- quais joins futuros ele viabiliza.

## Câmara dos Deputados

### `legislaturas`

- papel: dimensao de legislaturas
- o que extrai: lista de legislaturas da Câmara
- por que existe no projeto: define o recorte institucional correto antes de
  buscar deputados e despesas
- joins futuros: `id_legislatura`

### `deputados`

- papel: dimensao e ponte `deputado x legislatura`
- o que extrai: deputados vinculados a cada legislatura
- por que existe no projeto: permite descobrir quais deputados são validos em
  cada periodo e evita pedir despesas para combinacoes historicas incoerentes
- joins futuros: `id_deputado`, `id_legislatura`, `sigla_uf`, `sigla_partido`

### `deputados_despesas`

- papel: fato de despesa parlamentar
- o que extrai: despesas de deputados federais
- por que existe no projeto: e uma das bases centrais de gasto politico do
  projeto
- joins futuros: `id_deputado`, `documento_fornecedor_normalizado`,
  `cnpj_base_fornecedor`, `ano`

## Senado Federal

### `ceaps`

- papel: fato de despesa parlamentar
- o que extrai: despesas CEAPS dos senadores
- por que existe no projeto: complementa a camada de gasto parlamentar com a
  casa legislativa que faltava
- joins futuros: `documento_fornecedor_normalizado`, `cnpj_base_fornecedor`,
  `ano`

## SIOP

### `/sparql/` para itens de despesa orcamentaria

- papel: fato orcamentario
- o que extrai: itens de despesa da LOA com funcao, subfuncao, programa, acao,
  unidade, fonte, GND, modalidade, elemento e valores
- por que existe no projeto: fornece a camada de planejamento e classificacao
  orcamentaria para comparar com a execucao observada em outras fontes
- joins futuros: `codigo_funcao`, `codigo_subfuncao`, `codigo_programa`,
  `codigo_acao`, `codigo_unidade`, `codigo_fonte`, `codigo_gnd`,
  `codigo_modalidade`, `codigo_elemento`, `ano`

## Portal da Transparência

### `/api-de-dados/despesas/documentos-por-favorecido`

- papel: detalhamento documental por fornecedor
- o que extrai: documentos de despesa associados a um favorecido
- por que existe no projeto: aprofunda o fornecedor já observado em Câmara e
  Senado; não e a base principal, e a camada de drill-down documental
- joins futuros: `documento`, `cnpj_base`, identificadores de documento,
  periodo, orgao

### `/api-de-dados/ceis`

- papel: compliance e risco
- o que extrai: registros do CEIS
- por que existe no projeto: ajuda a verificar se fornecedores recorrentes
  aparecem em cadastros de sancao
- joins futuros: `documento`, `cnpj_base`

### `/api-de-dados/cnep`

- papel: compliance e risco
- o que extrai: registros do CNEP
- por que existe no projeto: amplia a camada de sancoes e responsabilizacao
- joins futuros: `documento`, `cnpj_base`

### `/api-de-dados/cepim`

- papel: compliance e risco
- o que extrai: registros do CEPIM
- por que existe no projeto: adiciona contexto de impedimento para entidades
  privadas sem fins lucrativos
- joins futuros: `documento`, `cnpj_base`

### `/api-de-dados/notas-fiscais`

- papel: documento fiscal
- o que extrai: notas fiscais associadas a fornecedores
- por que existe no projeto: aproxima a analise do documento comercial e ajuda
  a confrontar despesa, fornecedor e nota
- joins futuros: `documento`, `cnpj_base`, chaves de nota fiscal

## IBGE Localidades

### `regioes`

- papel: dimensao territorial
- o que extrai: lista de regioes do IBGE
- por que existe no projeto: normaliza o nivel regional dos joins
- joins futuros: `id`, `sigla`, relacoes territoriais superiores

### `estados`

- papel: dimensao territorial
- o que extrai: lista de UFs
- por que existe no projeto: padroniza UF entre bases que usam nome, sigla ou
  codigo
- joins futuros: `id`, `sigla`, `nome`

### `municipios`

- papel: dimensao territorial
- o que extrai: lista de municipios
- por que existe no projeto: padroniza codigos e nomes municipais para cruzar
  transferencias, entes, obras e fornecedores
- joins futuros: `id`, `nome`, hierarquia territorial

## PNCP

### `/v1/contratos`

- papel: contratacao pública
- o que extrai: contratos publicados no PNCP
- por que existe no projeto: liga fornecedor a contratacao pública formal
- joins futuros: CNPJ do fornecedor, numero do contrato, unidade compradora

### `/v1/atas`

- papel: contratacao pública
- o que extrai: atas registradas no PNCP
- por que existe no projeto: complementa a leitura de compras publicas e
  permite verificar fornecedores presentes em atas e contratos
- joins futuros: fornecedor, numero da ata, unidade compradora

### `/v1/pca/`

- papel: planejamento de contratacao
- o que extrai: PCA
- por que existe no projeto: adiciona a camada de planejamento da compra antes
  do contrato
- joins futuros: unidade compradora, classificacoes e codigos de planejamento

## Transferegov

### Grupo `especial`

- papel: transferencia federal
- recursos: `programa_especial`, `plano_acao_especial`, `executor_especial`,
  `empenho_especial`, `ordem_pagamento_ordem_bancaria_especial`,
  `historico_pagamento_especial`
- por que existe no projeto: permite seguir o fluxo da transferencia especial
  da programacao ate o pagamento
- joins futuros: programa, plano de acao, executor, empenho, ordem bancaria

### Grupo `fundoafundo`

- papel: transferencia federal
- recursos: `programa`, `plano_acao`, `empenho`, `relatorio_gestao`
- por que existe no projeto: cobre um tipo de transferencia diferente da
  especial, com foco em repasse e gestao
- joins futuros: programa, plano de acao, id de ente, empenho

### Grupo `ted`

- papel: transferencia federal
- recursos: `programa`, `plano_acao`, `termo_execucao`, `nota_credito`,
  `programacao_financeira`, `trf`
- por que existe no projeto: ajuda a reconstruir a execucao de transferencias
  entre unidades da administracao
- joins futuros: termo de execucao, nota de credito, TRF, plano de acao

## ObrasGov

### `/projeto-investimento`

- papel: cadastro mestre de obra ou investimento
- o que extrai: projetos de investimento
- por que existe no projeto: fornece o identificador central da obra e o
  contexto territorial e institucional
- joins futuros: `idUnico`, codigos de tomador, executor e repassador

### `/execucao-fisica`

- papel: fato de execucao fisica
- o que extrai: andamento fisico do projeto
- por que existe no projeto: permite confrontar dinheiro informado com entrega
  fisica observada
- joins futuros: `idProjetoInvestimento`, `idUnico` e campos de etapa

### `/execucao-financeira`

- papel: fato de execucao financeira
- o que extrai: informacoes financeiras do projeto
- por que existe no projeto: permite confrontar transferencia, empenho e gasto
  ligado a obra
- joins futuros: `idProjetoInvestimento`, `nrNotaEmpenho`, `ugEmitente`

### `/geometria`

- papel: dimensao espacial
- o que extrai: geometria de projetos já conhecidos
- por que existe no projeto: adiciona localizacao espacial para analise
  territorial e visualizacao
- joins futuros: `idUnico`

## Siconfi

### `entes`

- papel: dimensao de entes federativos
- o que extrai: cadastro de entes com identificadores como codigo IBGE, CNPJ,
  UF, esfera e nome
- por que existe no projeto: não e a evidencia final da inconsistencia; ele
  existe para normalizar o ente e permitir os joins dos demais recursos do
  Siconfi e de outras fontes
- por que entra no pipeline completo: e barato, estavel, não exige filtros e
  prepara a base de identificacao para as consultas futuras
- joins futuros: `payload.cod_ibge`, `payload.cnpj`, `payload.uf`, `id_ente`

### `extrato_entregas`

- papel: controle de entrega declaratoria
- o que extrai: informacoes de entregas vinculadas ao ente e ao ano de
  referencia
- por que existe no projeto: ajuda a diferenciar ausencia de dado de ausencia
  de entrega ou publicacao
- joins futuros: `id_ente`, `an_referencia`

### `msc_orcamentaria`

- papel: fato contabil-orcamentario
- o que extrai: informacoes da matriz de saldos contabeis orcamentaria
- por que existe no projeto: permite confrontar transferencias e pagamentos com
  registro contabil do ente
- joins futuros: `id_ente`, `an_referencia`, `me_referencia`,
  `co_tipo_matriz`, `classe_conta`, `id_tv`

### `msc_controle`

- papel: fato contabil de controle
- o que extrai: informacoes da MSC de controle
- por que existe no projeto: complementa a leitura contabil com outra classe de
  contas
- joins futuros: `id_ente`, `an_referencia`, `me_referencia`,
  `co_tipo_matriz`, `classe_conta`, `id_tv`

### `msc_patrimonial`

- papel: fato contabil patrimonial
- o que extrai: informacoes da MSC patrimonial
- por que existe no projeto: ajuda a observar reflexos patrimoniais de eventos
  financeiros
- joins futuros: `id_ente`, `an_referencia`, `me_referencia`,
  `co_tipo_matriz`, `classe_conta`, `id_tv`

### `rreo`

- papel: demonstrativo fiscal
- o que extrai: dados do RREO
- por que existe no projeto: oferece a camada declaratoria de demonstrativos
  fiscais periodicos
- joins futuros: `id_ente`, `an_exercicio`, `nr_periodo`,
  `co_tipo_demonstrativo`

### `rgf`

- papel: demonstrativo fiscal
- o que extrai: dados do RGF
- por que existe no projeto: complementa o RREO com outro demonstrativo fiscal
  oficial
- joins futuros: `id_ente`, `an_exercicio`, `nr_periodo`,
  `co_tipo_demonstrativo`, `co_poder`

### `dca`

- papel: demonstrativo fiscal
- o que extrai: dados da DCA
- por que existe no projeto: adiciona outra camada declaratoria para
  reconciliacao e verificacao de consistencia
- joins futuros: `id_ente`, `an_exercicio`

## ANP

### `/v1/combustivel`

- papel: validação cadastral de fornecedor
- o que extrai: revendedores autorizados de combustivel
- por que existe no projeto: testa se um fornecedor usado em despesa com
  combustivel aparece como revendedor autorizado
- joins futuros: CNPJ do fornecedor

### `/v1/glp`

- papel: validação cadastral de fornecedor
- o que extrai: revendedores autorizados de GLP
- por que existe no projeto: amplia a verificacao para outro tipo de
  estabelecimento regulado
- joins futuros: CNPJ do fornecedor

## Regra pratica

Nem todo endpoint do projeto tem o mesmo papel.

- alguns são espinha dorsal: `deputados_despesas`, `ceaps`, SIOP,
  Transferegov, ObrasGov, `msc_*`, `rreo`, `rgf`, `dca`
- alguns são dimensoes para join: `legislaturas`, `deputados`, IBGE,
  `entes`
- alguns são enriquecimento e compliance: Portal da Transparência, ANP

Se surgir a duvida "por que esse recurso esta no pipeline?", a resposta deve
ser encontrada aqui de forma direta, e não inferida do codigo.
