# ANP Revendedores

Documentação técnica do módulo de consulta de revendedores autorizados da ANP.

Arquivo principal:

- `extracao/anp/revendedores.py`

## Objetivo

Validar se fornecedores encontrados no projeto aparecem como revendedores autorizados de:

- combustivel
- GLP

Esse módulo e especialmente util para despesas parlamentares com combustível.

## Comando

```bash
uv run python main.py extrair-anp --datasets combustivel glp --min-ocorrencias 2 --limit-fornecedores 500
```

## Fonte de seed

O módulo usa a dimensão consolidada de fornecedores do Portal:

- `data/portal_transparencia/dimensoes/fornecedores.jsonl`

Ele consulta apenas fornecedores classificados como `cnpj`.

## Saídas

- `data/anp/revendedores/combustivel/fornecedor=<cnpj>.json`
- `data/anp/revendedores/glp/fornecedor=<cnpj>.json`

## Estratégia

- fan-out por CNPJ
- paginação por `numeropagina`
- envelope `_meta + payload`
- concorrência limitada
- sem revalidação imediata de consultas vazias
- cadência conservadora para reduzir erro `429`
- consultas vazias não deixam `.empty` residual para não bloquear reruns futuros

## Campos importantes para joins

No `_meta`:

- `documento`
- `dataset`

No payload, os campos devem ser tratados conforme a resposta oficial da ANP para:

- identificação do estabelecimento
- município
- UF
- situação cadastral
- data de autorização

## Join sugerido

- fornecedor: `_meta.documento`
- validação geográfica: campos de município e UF do payload ANP
