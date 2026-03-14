# Portal da Transparência

Documentação técnica do módulo de enriquecimento via Portal da Transparência.

Arquivos principais:

- `extracao/portal/base.py`
- `extracao/portal/fornecedores.py`
- `extracao/portal/documentos_favorecido.py`
- `extracao/portal/sancoes.py`
- `extracao/portal/notas_fiscais.py`
- `pipeline_portal.py`

## Objetivo

Enriquecer os fornecedores encontrados em Câmara e Senado com:

- documentos por favorecido
- sanções CEIS, CNEP e CEPIM
- notas fiscais

## Requisito

Definir uma chave da API:

```bash
export PORTAL_TRANSPARENCIA_API_KEY='sua-chave'
```

## Etapas

### 1. Construir dimensao de fornecedores

```bash
uv run python main.py portal-construir-fornecedores --min-ocorrencias 2
```

Saída:

- `data/portal_transparencia/dimensoes/fornecedores.jsonl`

### 2. Documentos por favorecido

```bash
uv run python main.py extrair-portal-documentos --limit-fornecedores 100 --ano-inicio 2023 --ano-fim 2026 --fases 1 2 3
```

Saída:

- `data/portal_transparencia/documentos_por_favorecido/...`

### 3. Sanções

```bash
uv run python main.py extrair-portal-sancoes --limit-fornecedores 100
```

Saída:

- `data/portal_transparencia/sancoes/...`

### 4. Notas fiscais

```bash
uv run python main.py extrair-portal-notas-fiscais --limit-fornecedores 100
```

Saída:

- `data/portal_transparencia/notas_fiscais/...`

## Estratégia do crawler

- sessão direta sem proxy
- sessão HTTP por thread
- rate limit por faixa horaria e por endpoint restrito
- envelope `_meta + payload`
- reprocessamento quando o arquivo antigo não tem o esquema novo de metadados
- concorrência limitada com infraestrutura compartilhada

## Infraestrutura compartilhada

O módulo do Portal reaproveita:

- `extracao/portal/base.py` para autenticação, rate limit oficial e retomada paginada
- `infra/estado/arquivos.py` para derivacao de `.tmp`, `.state.json` e `.empty`
- `infra/concorrencia.py` para execução paralela com backpressure e contadores thread-safe

Com isso, `documentos_favorecido`, `sancoes` e `notas_fiscais` deixaram de manter implementações quase iguais de controle de futures e estatisticas.

## Campos importantes para joins

Na dimensão de fornecedores:

- `documento`
- `tipo_documento`
- `cnpj_base`
- `nome_principal`
- `nomes_alternativos`
- `fontes`
- `anos`

Nos arquivos dos endpoints:

- `_meta.documento`
- `_meta.tipo_documento`
- `_meta.cnpj_base`
- `_meta.dataset`
- `_meta.nome_endpoint`
- `_meta.orgao_origem`
- `_meta.endpoint`

## Join sugerido

- fornecedor: `_meta.documento` ou `_meta.cnpj_base`
- selecao analitica: `nome_endpoint`, `dataset`, `fase`, `ano`
