# Siconfi

Documentação técnica do módulo de extracao da API de dados abertos do Siconfi.

Arquivos principais:

- `extracao/siconfi/__init__.py`
- `extracao/siconfi/config.py`
- `extracao/siconfi/specs.py`
- `extracao/siconfi/filtros.py`
- `extracao/siconfi/tarefas.py`

## Objetivo

Extrair bases fiscais e contabeis de entes subnacionais para confrontar:

- o que foi transferido
- o que foi registrado contabilmente
- o que foi informado em demonstrativos fiscais

## Comando

```bash
uv run python main.py extrair-siconfi --recursos entes
uv run python main.py extrair-siconfi --recursos extrato_entregas --filtro id_ente=3550308 --filtro an_referencia=2024
uv run python main.py extrair-siconfi --recursos msc_orcamentaria --filtro id_ente=3550308 --filtro an_referencia=2024 --filtro me_referencia=12 --filtro co_tipo_matriz=MSCC --filtro classe_conta=6 --filtro id_tv=period_change
```

Quando os recursos exigirem filtros diferentes, prefira comandos separados. Um unico bloco de `--filtro` e compartilhado por todos os recursos selecionados na mesma execução.

## Recursos suportados

- `entes`
- `extrato_entregas`
- `msc_orcamentaria`
- `msc_controle`
- `msc_patrimonial`
- `rreo`
- `rgf`
- `dca`

## Estratégia

- paginação por `offset` e `limit`
- saída em JSON Lines com `_meta.filtros`
- preservação do payload bruto do Siconfi
- validação local dos filtros obrigatórios por recurso, antes da primeira request
- normalizacao de aliases comuns como `exercício -> an_referencia` e `cod_ibge -> id_ente`

## Organização

- `extracao.siconfi` expõe a orquestração pública `Siconfi`
- `config.py` concentra paginação e limites da API
- `specs.py` mantém o catálogo declarativo dos recursos
- `filtros.py` normaliza e valida contratos de filtros
- `tarefas.py` isola caminhos de saída e seleção final de recursos

## Filtros obrigatórios por recurso

- `entes`: nenhum filtro obrigatório
- `extrato_entregas`: `id_ente`, `an_referencia`
- `msc_orcamentaria`: `id_ente`, `an_referencia`, `me_referencia`, `co_tipo_matriz`, `classe_conta`, `id_tv`
- `msc_controle`: `id_ente`, `an_referencia`, `me_referencia`, `co_tipo_matriz`, `classe_conta`, `id_tv`
- `msc_patrimonial`: `id_ente`, `an_referencia`, `me_referencia`, `co_tipo_matriz`, `classe_conta`, `id_tv`
- `rreo`: `an_exercicio`, `nr_periodo`, `co_tipo_demonstrativo`, `id_ente`
- `rgf`: `an_exercicio`, `in_periodicidade`, `nr_periodo`, `co_tipo_demonstrativo`, `co_poder`, `id_ente`
- `dca`: `an_exercicio`, `id_ente`

## Aliases aceitos

Para reduzir erros de uso, o extrator aceita alguns aliases (apelidos) e os converte para o nome oficial da API:

- `cod_ibge -> id_ente`
- `exercício -> an_referencia` nos recursos `extrato_entregas` e `msc_*`
- `exercício -> an_exercicio` nos recursos `rreo`, `rgf` e `dca`
- `ano_referencia -> an_referencia`
- `ano_exercicio -> an_exercicio`
- `mes` ou `mes_referencia -> me_referencia`
- `tipo_matriz -> co_tipo_matriz`
- `tipo_valor -> id_tv`

## Saídas

- `data/siconfi/<recurso>/consulta=<assinatura>.json`

## Campos importantes para joins

Exemplos observados em `entes`:

- `payload.cod_ibge`
- `payload.ente`
- `payload.uf`
- `payload.esfera`
- `payload.exercício`
- `payload.populacao`
- `payload.cnpj`

## Por que `entes` esta no pipeline completo

`entes` não entra no pipeline completo para "provar" uma inconsistencia por si
so. Ele entra por um motivo mais básico e mais importante:

- fornecer a dimensão de entes federativos usada para identificar corretamente
  município, estado, esfera e CNPJ;
- preparar os joins dos demais recursos do Siconfi, que em geral dependem de
  `id_ente`;
- oferecer uma base estavel e barata de extrair, sem filtros obrigatórios;
- reduzir ambiguidade quando o projeto cruzar Siconfi com IBGE, Transferegov,
  ObrasGov e outras fontes.

Em resumo:

- `entes` e uma dimensão de identificação;
- `msc_*`, `rreo`, `rgf` e `dca` são os recursos que carregam o conteúdo
  contabil e fiscal mais analítico.

Nos demais recursos, o join tende a usar:

- `id_ente`
- `an_referencia`
- `me_referencia`
- `co_tipo_matriz`
- `classe_conta`
- `id_tv`

## Join sugerido

- ente federativo: `payload.cod_ibge`, `payload.cnpj` ou `id_ente`
- comparação temporal: exercício, ano e mês de referência

## Observacoes operacionais

- `status=empty` nem sempre significa ausência de dados históricos; antes desta validação o caso mais comum era consulta incompleta.
- O crawler agora falha cedo com mensagem clara quando faltam filtros obrigatórios, evitando gastar requests com combinações inválidas.
