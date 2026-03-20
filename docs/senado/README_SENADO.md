# Senado Federal

Documentação técnica do módulo de extracao do Senado.

Arquivos principais:

- `extracao/senado/__init__.py`
- `extracao/senado/config.py`
- `extracao/senado/arquivos.py`
- `extracao/senado/dados.py`
- `extracao/senado/persistencia.py`
- `extracao/senado/tarefas.py`

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

## Organização

- `extracao.senado` expõe a orquestração pública `DadosSenado`
- `config.py` resolve endpoint e intervalo anual
- `arquivos.py` deriva artefatos anuais e valida saída reaproveitável
- `dados.py` normaliza o payload e enriquece registros
- `persistencia.py` isola a serialização anual
- `tarefas.py` concentra helpers puros de ordem e contagem

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
