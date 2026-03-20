# ObrasGov

Documentacão técnica do pacote de extração do ObrasGov.

Arquitetura:

- `extracao/obrasgov/__init__.py`: orquestração pública de `ObrasGov`.
- `extracao/obrasgov/config.py`: configuração estável e catálogo de recursos paginados.
- `extracao/obrasgov/projetos.py`: leitura local de projetos e `slug_id`.
- `extracao/obrasgov/tarefas.py`: caminhos de saída, validação de recursos e mapeamento de status.

## Objetivo

Capturar a camada física e financeira de investimentos em infraestrutura, especialmente para correlacionar:

- transferência
- obra
- executor
- geografia

## Invariantes de manutenção

- toda a orquestração pública do pacote fica em `extracao/obrasgov/__init__.py`;
- `config.py`, `projetos.py` e `tarefas.py` permanecem módulos auxiliares sem orquestração;
- recursos inválidos são ignorados com log de warning, sem interromper os válidos;
- não há compatibilidade com o módulo antigo `extracao/obrasgov/obras.py`.

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

## Estratégia

- recursos paginados por `pagina` e `tamanhoDaPagina`
- geometrias extraídas a partir dos `idUnico` já persistidos em projetos
- se a extração de `projeto-investimento` parar no meio, `extrair-obrasgov-geometrias` também aproveita os registros já gravados em `consulta=*.json.tmp`
- escrita em JSON Lines com envelope `_meta + payload`
- concorrência limitada para geometrias

## Saídas

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

Nas execuções:

- `payload.idProjetoInvestimento`
- `payload.nrNotaEmpenho`
- `payload.ugEmitente`

## Join sugerido

- projeto: `payload.idUnico`
- executor ou tomador: codigos CNPJ/identificadores presentes em arrays
- correlação financeira: `idProjetoInvestimento`, `nrNotaEmpenho`, `ugEmitente`
