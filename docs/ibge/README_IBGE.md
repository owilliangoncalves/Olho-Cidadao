# IBGE Localidades

Documentação técnica do módulo de extração da API de localidades do IBGE.

Arquitetura:

- `extracao/ibge/__init__.py`: orquestração pública de `LocalidadesIBGE`.
- `extracao/ibge/config.py`: catálogo de datasets e configuração estável do pacote.
- `extracao/ibge/tarefas.py`: resolução de datasets e caminhos de saída.

## Objetivo

Fornecer a camada de normalização territorial do projeto para joins entre:

- município
- UF
- região
- código IBGE

## Invariantes de manutenção

- toda a orquestração pública do pacote fica em `extracao/ibge/__init__.py`;
- `config.py` e `tarefas.py` devem permanecer módulos leves, sem rede;
- datasets inválidos são ignorados com log de warning, sem interromper o restante;
- não há compatibilidade com o módulo antigo `extracao/ibge/localidades.py`.

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
