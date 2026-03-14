# Documentacao Tecnica

Indice central da documentacao modular do projeto.

## Modulos de extracao

- [Camara](br_ETL/docs/camara/README_CAMARA.md)
- [Senado](br_ETL/docs/senado/README_SENADO.md)
- [SIOP](br_ETL/docs/siop/README_SIOP.md)
- [Portal da Transparencia](br_ETL/docs/portal_transparencia/README_PORTAL_TRANSPARENCIA.md)
- [PNCP](br_ETL/docs/pncp/README_PNCP.md)
- [Transferegov](br_ETL/docs/transferegov/README_TRANSFEREGOV.md)
- [ObrasGov](br_ETL/docs/obrasgov/README_OBRASGOV.md)
- [Siconfi](br_ETL/docs/siconfi/README_SICONFI.md)
- [IBGE](br_ETL/docs/ibge/README_IBGE.md)
- [ANP](br_ETL/docs/anp/README_ANP.md)

## Infraestrutura compartilhada

- [Base de APIs Publicas](br_ETL/docs/publica/README_PUBLICA.md)
- [Arquitetura](br_ETL/docs/ARCHITECTURE.md)
- [Endpoints e Relevancia](br_ETL/docs/README_ENDPOINTS_RELEVANCIA.md)

## Camada de entrada

- `main.py` e o ponto de entrada publico da CLI
- `cli/` concentra parser, handlers e bootstrap da interface de linha de comando
- `etl-config.toml` e a fonte de verdade da configuracao operacional do ETL
- `rodar-pipeline-completo` resolve parametros com precedencia `CLI -> [pipelines.completo]` em [etl-config.toml](br_ETL/etl-config.toml)
- `rodar-pipeline` e `rodar-paralelo` tambem delegam seus defaults operacionais ao `etl-config.toml`, em vez de embutirem anos, fontes ou janelas de datas no codigo
- o preflight desse comando apenas valida a configuracao final antes da execucao

## Convencoes gerais

- As extracoes novas persistem preferencialmente em JSON Lines.
- A estrategia de retomada do projeto e baseada em arquivos:
  `arquivo final + .tmp + .state.json + .empty`, conforme a natureza do endpoint.
- Nos conectores mais recentes, cada linha tende a seguir o envelope:

```json
{
  "_meta": {
    "orgao_origem": "origem_logica",
    "nome_endpoint": "dataset_logico",
    "endpoint": "/rota/oficial"
  },
  "payload": {}
}
```

- Os modulos antigos da Camara, Senado e SIOP continuam salvando registros achatados, mas agora com mais chaves derivadas para facilitar carga futura em banco.
