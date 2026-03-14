# Camara dos Deputados

Documentacao tecnica do modulo de extracao da Camara.

Arquivos principais:

- `extracao/camara/deputados_federais/extrator_legislatura.py`
- `extracao/camara/deputados_federais/deputados.py`
- `extracao/camara/deputados_federais/dependente.py`
- `extracao/camara/deputados_federais/camara.py`
- `pipeline.py`

## Objetivo

Extrair a cadeia base da Camara:

1. legislaturas
2. deputados por legislatura
3. despesas por deputado e por ano
4. consolidacao em CSV

## Fluxo

### 1. Legislaturas

Comando:

```bash
uv run python main.py baixar-legislaturas
```

Saida:

- `data/legislaturas.json`

### 2. Deputados por legislatura

Comando:

```bash
uv run python main.py extrair-legislaturas
```

Saida:

- `data/deputados_por_legislaturas/deputados_legislaturas_<id>.json`

### 3. Despesas por deputado

Comando:

```bash
uv run python main.py extrair-dependentes --endpoint deputados_despesas --ano-inicio 2023 --ano-fim 2026
```

Observacao:

- `ano-fim` e exclusivo

Saida:

- `data/despesas_deputados_federais/<ano>/despesas_<id>.json`

### 4. Consolidacao

Comando:

```bash
uv run python main.py gerar-csv
```

Saida:

- `data/csv/despesas.csv`

## Estrategia do crawler

- leitura progressiva de arquivos de deputados
- filtragem por janela temporal da legislatura
- priorizacao de anos mais recentes
- checkpoint por `(endpoint, deputado, ano)` em arquivos `.state.json`
- escrita incremental em JSON Lines com arquivo temporario `.tmp`
- marcador `.empty` para tarefas confirmadas como vazias
- reprocessamento automatico quando o arquivo antigo nao contem o esquema novo

## Campos importantes para banco e joins

Nos arquivos de despesas:

- `id_deputado`
- `id_legislatura`
- `nome_deputado`
- `uri_deputado`
- `sigla_uf_deputado`
- `sigla_partido_deputado`
- `cnpjCpfFornecedor`
- `documento_fornecedor_normalizado`
- `tipo_documento_fornecedor`
- `cnpj_base_fornecedor`
- `codDocumento`
- `codLote`
- `numDocumento`
- `dataDocumento`
- `valorDocumento`
- `valorLiquido`
- `orgao_origem`
- `endpoint_origem`

## Join sugerido

- fornecedor: `documento_fornecedor_normalizado` ou `cnpj_base_fornecedor`
- parlamentar: `id_deputado`
- recorte institucional: `id_legislatura`, `sigla_uf_deputado`, `sigla_partido_deputado`

## Pipeline completa

```bash
uv run python main.py rodar-pipeline
```

Se `--ano-inicio` e `--ano-fim` forem omitidos, o comando usa
`[config.pipelines.camara]` em
[etl-config.toml](br_ETL/etl-config.toml).
