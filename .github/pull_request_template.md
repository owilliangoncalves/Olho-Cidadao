## Resumo

Descreva o objetivo desta mudanca e o problema que ela resolve.

## Tipo de mudanca

- [ ] Correcao de bug
- [ ] Nova fonte ou enriquecimento de dados
- [ ] Refatoracao
- [ ] Documentação
- [ ] Aplicacao pública (`apps/cidadao_de_olho/`)

## Validacao

- [ ] `python -m ruff check .`
- [ ] `python -m unittest discover -s tests -v`
- [ ] `python -m py_compile $(rg --files -g '*.py')`
- [ ] `cargo test --manifest-path apps/cidadao_de_olho/Cargo.toml`
- [ ] `cd apps/cidadao_de_olho/ui && npm run build`

## Checklist

- [ ] Atualizei a documentacao relevante
- [ ] Nao inclui segredos, dados sensiveis ou artefatos locais
- [ ] Registrei riscos, tradeoffs ou passos manuais quando necessario
