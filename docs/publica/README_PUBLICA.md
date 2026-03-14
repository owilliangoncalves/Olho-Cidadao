# Base de APIs Publicas

Documentação da infraestrutura compartilhada usada pelos conectores mais novos do projeto.

Arquivo principal:

- `extracao/publica/base.py`

## Objetivo

Padronizar a extrção de APIs publicas que não fazem parte do núcleo original de Câmara, Senado e SIOP, reaproveitando:

- sessão HTTP direta sem proxy e por thread;
- rate limiting por origem;
- escrita incremental em JSON Lines;
- controle de arquivo temporário;
- retomada por arquivo de estado;
- envelope `_meta + payload`.

## Estratégia de persistência

Cada tarefa gera:

- arquivo final em `data/...`
- arquivo temporário `.tmp`
- arquivo de estado em `data/_estado/publica/...`
- marcador `.empty` quando a consulta não retorna itens

Quando um arquivo final já existe e o primeiro registro contém os metadados mínimos esperados, a tarefa e pulada.

Os caminhos de artefatos agora são derivados por helper compartilhado da camada de estado, evitando divergência entre conectores.

## Modos de paginação suportados

### 1. Paginação por pagina

Usada quando a API trabalha com parametros como:

- `pagina`
- `tamanhoPagina`
- `tamanhoDaPagina`

### 2. Paginação por offset

Usada quando a API trabalha com:

- `offset`
- `limit`

## Envelope padrão

Os conectores baseados nessa infraestrutura gravam um envelope minimo por linha:

```json
{
  "_meta": {
    "endpoint": "/rota/oficial",
    "orgao_origem": "sigla_logica",
    "nome_endpoint": "dataset_logico"
  },
  "payload": {}
}
```

O `_meta` recebe campos adicionais conforme o módulo, por exemplo:

- `dataset`
- `filtros`
- `documento`
- `id_unico`
- `data_inicial`
- `data_final`

A validação de reuso também passou a olhar diretamente para `_meta`, em vez de cada módulo implementar sua própria leitura do primeiro registro.

## Concorrencia

Os conectores que agendam varias tarefas independentes passaram a compartilhar:

- contador thread-safe de `completed/skipped/empty/failed`
- executor com `max_workers` e `max_pending`
- backpressure local padronizado

Essa infraestrutura fica em `infra/concorrencia.py` e e reutilizada por módulos como ObrasGov e ANP.

## Quando usar essa base

Use `ExtratorAPIPublicaBase` para novas integrações que:

- exponham JSON;
- tenham volume paginado;
- possam ser consumidas com `GET`;
- precisem de saída idempotente e reprocessamento seguro.

## Quando não usar

Evite essa base quando:

- a API exigir autenticação especial complexa;
- a resposta não for JSON;
- o fluxo depender de navegacao altamente especifica entre endpoints;
- a fonte já tiver um extrator legado especializado no projeto.
