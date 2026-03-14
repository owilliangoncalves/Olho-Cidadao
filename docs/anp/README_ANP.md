# ANP Revendedores

Documentacao tecnica do modulo de consulta de revendedores autorizados da ANP.

Arquivo principal:

- `extracao/anp/revendedores.py`

## Objetivo

Validar se fornecedores encontrados no projeto aparecem como revendedores autorizados de:

- combustivel
- GLP

Esse modulo e especialmente util para despesas parlamentares com combustivel.

## Comando

```bash
uv run python main.py extrair-anp --datasets combustivel glp --min-ocorrencias 2 --limit-fornecedores 500
```

## Fonte de seed

O modulo usa a dimensao consolidada de fornecedores do Portal:

- `data/portal_transparencia/dimensoes/fornecedores.jsonl`

Ele consulta apenas fornecedores classificados como `cnpj`.

## Saidas

- `data/anp/revendedores/combustivel/fornecedor=<cnpj>.json`
- `data/anp/revendedores/glp/fornecedor=<cnpj>.json`

## Estrategia

- fan-out por CNPJ
- paginacao por `numeropagina`
- envelope `_meta + payload`
- concorrencia limitada
- sem revalidacao imediata de consultas vazias
- cadencia conservadora para reduzir `429`
- consultas vazias nao deixam `.empty` residual para nao bloquear reruns futuros

## Campos importantes para joins

No `_meta`:

- `documento`
- `dataset`

No payload, os campos devem ser tratados conforme a resposta oficial da ANP para:

- identificacao do estabelecimento
- municipio
- UF
- situacao cadastral
- data de autorizacao

## Join sugerido

- fornecedor: `_meta.documento`
- validacao geografica: campos de municipio e UF do payload ANP
