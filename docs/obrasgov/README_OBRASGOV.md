# ObrasGov

Documentacao tecnica do modulo de extracao do ObrasGov.

Arquivo principal:

- `extracao/obrasgov/obras.py`

## Objetivo

Capturar a camada fisica e financeira de investimentos em infraestrutura, especialmente para correlacionar:

- transferencia
- obra
- executor
- geografia

## Recursos suportados

- `projeto-investimento`
- `execucao-fisica`
- `execucao-financeira`
- `geometria`

## Comandos

### Recursos paginados

```bash
uv run python main.py extrair-obrasgov --recursos projeto-investimento execucao-fisica execucao-financeira --filtro uf=RS
```

### Geometrias

```bash
uv run python main.py extrair-obrasgov-geometrias --limit-ids 500
```

## Estrategia

- recursos paginados por `pagina` e `tamanhoDaPagina`
- geometrias extraidas a partir dos `idUnico` ja persistidos em projetos
- se a extracao de `projeto-investimento` parar no meio, `extrair-obrasgov-geometrias` tambem aproveita os registros ja gravados em `consulta=*.json.tmp`
- escrita em JSON Lines com envelope `_meta + payload`
- concorrencia limitada para geometrias

## Saidas

- `data/obrasgov/projeto-investimento/consulta=<assinatura>.json`
- `data/obrasgov/execucao-fisica/consulta=<assinatura>.json`
- `data/obrasgov/execucao-financeira/consulta=<assinatura>.json`
- `data/obrasgov/geometria/projeto=<id>.json`

## Campos importantes para joins

Nos projetos:

- `payload.idUnico`
- `payload.uf`
- `payload.tomadores[].codigo`
- `payload.executores[].codigo`
- `payload.repassadores[].codigo`
- `payload.dataCadastro`
- `payload.situacao`

Nas execucoes:

- `payload.idProjetoInvestimento`
- `payload.nrNotaEmpenho`
- `payload.ugEmitente`

## Join sugerido

- projeto: `payload.idUnico`
- executor ou tomador: codigos CNPJ/identificadores presentes em arrays
- correlacao financeira: `idProjetoInvestimento`, `nrNotaEmpenho`, `ugEmitente`
