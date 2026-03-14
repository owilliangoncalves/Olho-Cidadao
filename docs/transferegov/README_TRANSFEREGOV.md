# Transferegov

Documentação técnica dos crawlers do ecossistema Transferegov.

Arquivo principal:

- `extracao/transferegov/recursos.py`

## Objetivo

Extrair datasets das APIs:

- Transferencias Especiais
- Fundo a Fundo
- TED

para rastrear a passagem de recursos entre origem federal e destino executor.

## Comandos

### Transferencias Especiais

```bash
uv run python main.py extrair-transferegov-especial --recursos programa_especial plano_acao_especial --filtro ano_programa=2025
```

### Fundo a Fundo

```bash
uv run python main.py extrair-transferegov-fundo --recursos programa plano_acao --filtro id_ente=3550308
```

### TED

```bash
uv run python main.py extrair-transferegov-ted --recursos programa plano_acao trf --filtro id_ente=5300108
```

## Estratégia

- paginação por `offset` e `limit`
- filtros livres passados pela CLI via `--filtro chave=valor`
- saída em JSON Lines com `_meta.filtros`
- nomes de arquivos derivados do conjunto de filtros aplicados

## Saídas

- `data/transferegov/especial/<recurso>/consulta=<assinatura>.json`
- `data/transferegov/fundoafundo/<recurso>/consulta=<assinatura>.json`
- `data/transferegov/ted/<recurso>/consulta=<assinatura>.json`

## Recursos hoje suportados

### Especial

- `programa_especial`
- `plano_acao_especial`
- `executor_especial`
- `empenho_especial`
- `ordem_pagamento_ordem_bancaria_especial`
- `historico_pagamento_especial`

### Fundo a Fundo

- `programa`
- `plano_acao`
- `empenho`
- `relatorio_gestao`

### TED

- `programa`
- `plano_acao`
- `termo_execucao`
- `nota_credito`
- `programacao_financeira`
- `trf`

## Chaves analiticas esperadas

Como os payloads são mantidos brutos, o join futuro deve priorizar:

- identificadores internos do recurso
- codigos de ente
- codigos de programa e plano de acao
- numeros de empenho, nota de credito, ordem bancaria e termo de execucao

Os filtros aplicados ficam preservados no `_meta`, o que ajuda a reconstruir a origem exata da consulta.
