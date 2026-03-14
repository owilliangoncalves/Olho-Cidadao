# Contribuindo

## Pré-requisitos

- Python 3.14
- `uv` ou `pip`

## Setup local

```bash
uv sync
uv run python main.py --help
```

ou:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Checklist antes de abrir alteração

```bash
.venv/bin/ruff check .
.venv/bin/python -m unittest discover -s tests -v
python3 -m py_compile $(rg --files -g '*.py')
```

## Diretrizes de código

- Prefira JSON Lines para persistência incremental
- Mantenha a convenção `final + .tmp + .state.json + .empty`
- Evite carregar datasets completos em memória
- Preserve o payload bruto quando ele for relevante para auditoria
- Adicione chaves derivadas apenas quando elas facilitarem joins futuros
- Documente módulos novos em `docs/<fonte>/README_<FONTE>.md`

## Ao adicionar uma nova fonte

1. Crie ou reutilize uma base compartilhada de extração
2. Modele a unidade de trabalho de forma retomável
3. Defina um caminho de saída determinístico
4. Salve metadados mínimos de rastreabilidade
5. Atualize a CLI em `main.py`
6. Atualize `README.md` e `docs/README.md`
7. Adicione ao menos um teste sem rede cobrindo utilitário ou contrato local

## Escopo dos testes

Para manter o projeto estável sem depender de rede externa, priorizamos:

- utilitários puros
- contratos de naming
- persistência de estado
- conversões e consolidações locais
- smoke tests de import e CLI
