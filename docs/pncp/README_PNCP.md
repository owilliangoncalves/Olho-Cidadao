# PNCP

Documentação técnica do pacote de extração da consulta pública do PNCP.

Arquitetura:

- `extracao/pncp/__init__.py`: orquestração pública de `PNCPConsulta`.
- `extracao/pncp/config.py`: configuração estável e catálogo de recursos mensais.
- `extracao/pncp/tarefas.py`: janelas mensais, anos e caminhos de saída.

## Objetivo

Extrair:

- contratos
- atas
- PCA

para posterior correlação com fornecedores que aparecem em gastos parlamentares e outras bases.

## Invariantes de manutenção

- toda a orquestração pública do pacote fica em `extracao/pncp/__init__.py`;
- `config.py` e `tarefas.py` devem permanecer módulos leves, sem rede;
- contratos e atas seguem janelas mensais; PCA segue corte anual;
- não há compatibilidade com o módulo antigo `extracao/pncp/consultas.py`.

## Comando

```bash
uv run python main.py extrair-pncp --data-inicial 2025-01-01 --data-final 2025-12-31 --tamanho-pagina 50
```

Opções relevantes:

- `--sem-contratos`
- `--sem-atas`
- `--sem-pca`
- `--codigo-classificacao-superior`

## Estratégia

- contratos e atas: janelas mensais
- PCA: processamento anual
- paginação por `pagina` e `tamanhoPagina`
- persistência em JSON Lines com envelope `_meta + payload`

## Saídas

- `data/pncp/contratos/ano=<ano>/mes=<mes>.json`
- `data/pncp/atas/ano=<ano>/mes=<mes>.json`
- `data/pncp/pca/ano=<ano>.json`

## Campos importantes para joins

No payload de contratos, exemplos observados:

- `numeroControlePncpCompra`
- `numeroControlePNCP`
- `orgaoEntidade.cnpj`
- `unidadeOrgao.codigoIbge`
- `unidadeOrgao.codigoUnidade`
- `niFornecedor`
- `nomeRazaoSocialFornecedor`
- `numeroContratoEmpenho`
- `anoContrato`
- `sequencialContrato`

No `_meta`:

- `dataset`
- `data_inicial`
- `data_final`
- `ano_pca`
- `codigo_classificacao_superior`

## Join sugerido

- fornecedor: `payload.niFornecedor`
- territorio: `payload.unidadeOrgao.codigoIbge`
- orgao comprador: `payload.orgaoEntidade.cnpj`
