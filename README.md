# Olho Cidadao

Plataforma para extração, consolidação e publicação de dados
públicos brasileiros.

Este repo reúne:

- um ETL em Python para fontes legislativas, orçamentárias, fiscais e de compras públicas
- uma aplicação pública em `apps/cidadao_de_olho/`, com backend `Loco.rs` e frontend `React + Vite`
- documentação modular por fonte, com foco em rastreabilidade operacional e evolução incremental

Na camada de entrada do ETL, `main.py` funciona como wrapper enxuto e a
orquestração pública da CLI fica concentrada em `cli/__init__.py`.

## Escopo atual

Fontes já integradas:

- Câmara dos Deputados
- Senado Federal
- SIOP
- Portal da Transparência
- PNCP
- Transferegov
- ObrasGov
- Siconfi
- IBGE
- ANP

## Funcionalidades

- Crawlers retomáveis: `arquivo final + .tmp + .state.json + .empty`
- Saída em JSON Lines para baixo uso de RAM e carga futura em banco
- Prioridade para reprocessamento idempotente e rastreabilidade
- Camada HTTP compartilhada com retry, backoff e rate limiting
- Organização por domínio, com documentação técnica por módulo
- CLI centralizada e infraestrutura compartilhada para concorrência e retomada

## Componentes principais

- `main.py`, `cli/`, `extracao/`, `infra/` e `utils/`: pipeline ETL e automação operacional
- `apps/cidadao_de_olho/`: aplicação pública que publica snapshots e visualizações
- `docs/`: documentação técnica por fonte e por camada do sistema

## Instalação

### Com `uv`

```bash
uv sync
uv run python main.py --help
```

Após a instalação, a entrada de console também fica disponível como:

```bash
br-etl --help
```

## Configuração

Os endpoints, parâmetros operacionais e defaults de execução são lidos de
[etl-config.toml](etl-config.toml).
Esse é o único arquivo de configuração suportado pela aplicação.

Variáveis de ambiente úteis:

```env
PROXIES=ip:porta:usuario:senha,ip:porta:usuario:senha
PORTAL_TRANSPARENCIA_API_KEY=sua_chave
LOG_LEVEL=INFO
```

Observações:

- `PROXIES` é opcional e não é usada por todas as fontes
- `PORTAL_TRANSPARENCIA_API_KEY` é obrigatória apenas para o módulo do Portal
- `LOG_LEVEL` controla a verbosidade global do projeto

## Comandos principais

Fluxo Câmara:

```bash
uv run python main.py baixar-legislaturas
uv run python main.py extrair-legislaturas
uv run python main.py extrair-dependentes --endpoint deputados_despesas --ano-inicio 2012 --ano-fim 2026
uv run python main.py gerar-csv
```

`gerar-csv` executa todos os geradores de CSV disponíveis sobre os dados já extraídos.

Pipelines:

```bash
uv run python main.py menu
uv run python main.py rodar-pipeline
uv run python main.py rodar-paralelo
uv run python main.py rodar-pipeline-completo
uv run python main.py rodar-pipeline-portal --limit-fornecedores 100
```

Menu interativo:

```bash
uv run python main.py menu
uv run python main.py abrir-menu
```

O menu interativo abre uma navegacao em terminal para explorar as principais
funcionalidades do projeto, com execucao dos comandos mais comuns sem exigir
que o usuario memorize toda a CLI.

Regras de resolução dos pipelines:

- `rodar-pipeline` usa `[config.pipelines.camara]` em [etl-config.toml](etl-config.toml) quando `--ano-inicio` e `--ano-fim` são omitidos
- `rodar-paralelo` usa `[config.pipelines.paralelo]` quando `--ano-inicio`, `--ano-fim`, `--pncp-data-inicial`, `--pncp-data-final` e `--max-workers` são omitidos
- em `rodar-paralelo`, os switches `--camara/--sem-camara`, `--senado/--sem-senado`, `--siop/--sem-siop`, `--ibge/--sem-ibge`, `--pncp/--sem-pncp`, `--transferegov/--sem-transferegov`, `--obrasgov/--sem-obrasgov` e `--siconfi/--sem-siconfi` sobrescrevem `[config.pipelines.paralelo.fontes]` apenas na execução atual
- a precedência é sempre `CLI -> etl-config.toml`

O comando `rodar-pipeline-completo` lê sua configuração da seção
`[pipelines.completo]` em [etl-config.toml](etl-config.toml),
e a CLI serve apenas para sobrescrever alguns parâmetros mais usados.
Subseções como `senado`, `ibge`, `siconfi`, `portal` e `anp` também controlam
os detalhes operacionais do comando completo.

Regras de resolução dos parâmetros do pipeline completo:

- `--ano-inicio` e `--ano-fim` passados na CLI têm prioridade sobre `etl-config.toml`
- se a CLI não informar esses parâmetros, o comando usa `[pipelines.completo]`
- hoje, os valores versionados no repositório são `ano_inicio = 2012` e `ano_fim = 2026`
- o preflight não define esses valores; ele apenas valida se a configuração resultante é coerente antes de iniciar qualquer extração

Exemplos:

```bash
uv run python main.py rodar-pipeline-completo
uv run python main.py rodar-pipeline-completo --ano-inicio 2020 --ano-fim 2024
uv run python main.py rodar-paralelo --sem-siop --max-workers 6
```

No primeiro caso, o comando usa os valores de
[etl-config.toml](etl-config.toml).
No segundo, usa os valores informados na CLI apenas para essa execução.
No terceiro, mantém os defaults de `[config.pipelines.paralelo]`, mas desabilita `siop`
e ajusta `max_workers` apenas nesse run.

O preflight do pipeline completo verifica, antes da fase de extração:

- se `ano_inicio < ano_fim`
- se `max_workers >= 1`
- se a chave do Portal foi definida quando o Portal está habilitado

Outras fontes:

```bash
uv run python main.py extrair-senado
uv run python main.py extrair-siop
uv run python main.py extrair-ibge-localidades
uv run python main.py extrair-pncp --data-inicial 2025-01-01 --data-final 2025-12-31
uv run python main.py extrair-transferegov-especial
uv run python main.py extrair-obrasgov
uv run python main.py extrair-siconfi --recursos entes
uv run python main.py extrair-siconfi --recursos extrato_entregas --filtro id_ente=3550308 --filtro an_referencia=2024
uv run python main.py extrair-anp
```

## Convenções de saída e retomada

O projeto usa estas convenções de forma padronizada:

- arquivo final: resultado consolidado e reaproveitável
- `.tmp`: escrita parcial ainda não promovida
- `.state.json`: checkpoint da unidade de trabalho
- `.empty`: marcador transitório de consulta vazia, usado para disparar uma revalidação e removido depois dela

Exemplos:

- `data/despesas_deputados_federais/2025/despesas_123.json`
- `data/_estado/camara/endpoint=deputados_despesas/ano=2025/id=123.state.json`
- `data/orcamento_item_despesa/_particoes/ano=2025/funcao=10.json`
- `data/siconfi/entes/consulta=all.json`

## Estrutura do projeto

```text
.
├── apps/
│   └── cidadao_de_olho/
├── cli/
├── configuracao/
├── docs/
├── extracao/
├── infra/
├── tests/
├── utils/
├── etl-config.toml
├── main.py
├── pipeline/
└── pyproject.toml
```

## Desenvolvimento

Lint:

```bash
.venv/bin/ruff check .
```

Testes:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Smoke checks úteis:

```bash
.venv/bin/python main.py --help
python3 -m py_compile $(rg --files -g '*.py')
```

## Documentação

- interface pública e API web: [apps/cidadao_de_olho/README.md](apps/cidadao_de_olho/README.md)
- índice técnico do ETL: [docs/README.md](docs/README.md)

Leituras recomendadas:

- [Arquitetura](docs/ARCHITECTURE.md)
- [Endpoints e Relevancia](docs/README_ENDPOINTS_RELEVANCIA.md)
- [Câmara](docs/camara/README_CAMARA.md)
- [Senado](docs/senado/README_SENADO.md)
- [SIOP](docs/siop/README_SIOP.md)
- [Base Pública](docs/publica/README_PUBLICA.md)

## Comunidade

- Guia de contribuição: [CONTRIBUTING.md](CONTRIBUTING.md)
- Código de conduta: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Política de segurança: [SECURITY.md](SECURITY.md)
- Canais de suporte e uso: [SUPPORT.md](SUPPORT.md)
