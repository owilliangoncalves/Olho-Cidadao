# Documentação Tecnica

Indice central da documentacao modular do projeto.

## Modulos de extracao

- [Câmara](./camara/README_CAMARA.md)
- [Senado](./senado/README_SENADO.md)
- [SIOP](./siop/README_SIOP.md)
- [Portal da Transparencia](./portal_transparencia/README_PORTAL_TRANSPARENCIA.md)
- [PNCP](./pncp/README_PNCP.md)
- [Transferegov](./transferegov/README_TRANSFEREGOV.md)
- [ObrasGov](./obrasgov/README_OBRASGOV.md)
- [Siconfi](./siconfi/README_SICONFI.md)
- [IBGE](./ibge/README_IBGE.md)
- [ANP](./anp/README_ANP.md)

## Infraestrutura compartilhada

- [Base de APIs Publicas](./publica/README_PUBLICA.md)
- [Arquitetura](./ARCHITECTURE.md)
- [Endpoints e Relevancia](./README_ENDPOINTS_RELEVANCIA.md)

## Camada de entrada

- `main.py` e o ponto de entrada publico da CLI
- `cli/` concentra parser, handlers e bootstrap da interface de linha de comando
- `etl-config.toml` e a fonte de verdade da configuracao operacional do ETL
- `rodar-pipeline-completo` resolve parametros com precedencia `CLI -> [pipelines.completo]` em [etl-config.toml](../etl-config.toml)
- `rodar-pipeline` e `rodar-paralelo` também delegam seus defaults operacionais ao `etl-config.toml`, em vez de embutirem anos, fontes ou janelas de datas no codigo
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

- Os módulos antigos da Câmara, Senado e SIOP continuam salvando registros achatados, mas agora com mais chaves derivadas para facilitar carga futura em banco.
