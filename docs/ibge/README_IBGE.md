# IBGE Localidades

Documentacao tecnica do modulo de extracao da API de localidades do IBGE.

Arquivo principal:

- `extracao/ibge/localidades.py`

## Objetivo

Fornecer a camada de normalizacao territorial do projeto para joins entre:

- municipio
- UF
- regiao
- codigo IBGE

## Comando

```bash
uv run python main.py extrair-ibge-localidades --datasets estados municipios
```

Se nenhum dataset for informado, o modulo extrai:

- `regioes`
- `estados`
- `municipios`

## Saidas

- `data/ibge/localidades/regioes.json`
- `data/ibge/localidades/estados.json`
- `data/ibge/localidades/municipios.json`

## Estrategia

- consulta direta sem proxy
- chamadas nao paginadas
- persistencia em JSON Lines com `_meta + payload`

## Campos importantes para joins

Nos estados:

- `payload.id`
- `payload.sigla`
- `payload.nome`
- `payload.regiao.id`

Nos municipios:

- `payload.id`
- `payload.nome`
- `payload.microrregiao.mesorregiao.UF.sigla`

## Join sugerido

- territorio: `codigoIbge`, `cod_ibge` ou `payload.id`
- UF: `sigla`, `uf`, `ufSigla`
