# Contribuindo

Obrigado por considerar uma contribuição para o Olho Cidadao.

## Formas de contribuir

- reportar bugs, regressões ou comportamentos inesperados
- propor novas fontes, recortes e enriquecimentos de dados
- melhorar documentação, testes, observabilidade e UX da CLI
- evoluir a aplicação pública em `apps/cidadao_de_olho/`

## Pré-requisitos

- Python 3.14
- `uv` ou `pip`

Se você também for mexer na aplicação pública:

- Rust estável
- Node.js 24

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

Para a aplicação pública:

```bash
cargo test --manifest-path apps/cidadao_de_olho/Cargo.toml
cd apps/cidadao_de_olho/ui
npm ci
npm run build
```

## Fluxo recomendado

1. Abra uma issue antes de mudanças grandes, novas fontes ou alterações estruturais.
2. Faça mudanças pequenas e focadas, com contexto suficiente para revisão.
3. Atualize a documentação quando houver alteração de comportamento, contrato ou configuração.
4. Rode os checks locais antes de abrir o pull request.
5. Use o template de PR para registrar escopo, validação e riscos.

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
- Evite misturar refatoração ampla com adição de fonte nova no mesmo PR

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
- builds locais do frontend e testes do backend web quando a mudança tocar `apps/cidadao_de_olho/`
