# IBGE Localidades

Documentação técnica do módulo de extração da API de localidades do IBGE.

Arquivo principal:

- `extracao/ibge/localidades.py`

## Objetivo

Fornecer a camada de normalização territorial do projeto para joins entre:

- município
- UF
- região
- código IBGE

## Comando

```bash
uv run python main.py extrair-ibge-localidades --datasets estados municipios
```

Se nenhum dataset for informado, o módulo extrai:

- `regioes`
- `estados`
- `municipios`

## Saídas

- `data/ibge/localidades/regioes.json`
- `data/ibge/localidades/estados.json`
- `data/ibge/localidades/municipios.json`

## Estratégia

- consulta direta sem proxy
- chamadas não páginadas
- persistiência em JSON Lines com `_meta + payload`

## Campos importantes para joins

Nos estados:

- `payload.id`
- `payload.sigla`
- `payload.nome`
- `payload.regiao.id`

Nos municípios:

- `payload.id`
- `payload.nome`
- `payload.microrregiao.mesorregiao.UF.sigla`

## Join sugerido

- territorio: `codigoIbge`, `cod_ibge` ou `payload.id`
- UF: `sigla`, `uf`, `ufSigla`
