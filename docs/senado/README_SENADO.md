# Senado Federal

Documentação técnica do módulo de extracao do Senado.

Arquivo principal:

- `extracao/senado/senadores.py`

## Objetivo

Extrair o CEAPS do Senado por exercício, com persistência em JSON Lines e escrita atomica.

## Comando

```bash
uv run python main.py extrair-senado --endpoint ceaps
```

## Saída

- `data/senadores/ceaps_<ano>.json`

## Estratégia do crawler

- processamento do ano mais recente para o mais antigo
- pulos automáticos quando o arquivo final já existe no esquema novo
- escrita em arquivo temporário `.tmp`
- arquivo de estado `.state.json` por ano
- marcador `.empty` para anos sem dados
- promocao atomica para o arquivo final

## Campos importantes para banco e joins

- `id`
- `codSenador`
- `nomeSenador`
- `fornecedor`
- `cpfCnpj`
- `documento_fornecedor_normalizado`
- `tipo_documento_fornecedor`
- `cnpj_base_fornecedor`
- `documento`
- `data`
- `tipoDespesa`
- `valorReembolsado`
- `ano`
- `ano_arquivo`
- `orgao_origem`
- `endpoint_origem`

## Join sugerido

- fornecedor: `documento_fornecedor_normalizado`
- comparacao temporal: `ano`, `ano_arquivo`, `data`
- ator politico: `codSenador`
