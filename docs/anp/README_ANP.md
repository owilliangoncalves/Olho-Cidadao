# ANP Revendedores

Documentação técnica do módulo de consulta de revendedores autorizados da ANP.

Arquitetura:

- `extracao/anp/__init__.py`: fachada pública do pacote e orquestrador `RevendedoresANP`.
- `extracao/anp/config.py`: constantes e configuração operacional.
- `extracao/anp/documentos.py`: carga e deduplicação da seed de CNPJs.
- `extracao/anp/tarefas.py`: expansão de tarefas, caminhos de saída e mapeamento de status.

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

## Fluxo de execução

1. `RevendedoresANP` carrega a configuração da ANP.
2. A seed local de fornecedores é reconstruída e lida do Portal.
3. Apenas CNPJs válidos e deduplicados seguem para consulta.
4. O pacote expande `dataset x documento` em tarefas concorrentes.
5. Cada resposta é persistida em JSON com envelope `_meta + payload`.

## Invariantes de manutenção

- a orquestração do pacote fica em `extracao/anp/__init__.py`;
- a importação de `extracao.anp` precisa continuar leve para não acoplar a CLI ao cliente HTTP;
- `documentos.py` e `tarefas.py` devem permanecer puros, sem rede nem I/O externo além de caminhos calculados;
- consultas vazias não deixam `.empty` residual para não bloquear reruns.

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
