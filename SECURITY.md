# Segurança

## Relato responsável

Se você identificar uma vulnerabilidade, problema de vazamento de credenciais ou risco operacional relevante, não publique a falha diretamente em issue pública.

Abra um canal privado com o mantenedor do repositório e inclua:

- descrição do problema
- impacto esperado
- passos mínimos para reproduzir
- evidências sanitizadas

## Boas práticas deste repositório

- segredos devem ficar fora do repositório
- use `.env` local para chaves e proxies
- dados brutos extraídos não devem conter credenciais
- artefatos de `data/` e `logs/` não devem ser versionados
- endpoints com limite oficial devem respeitar rate limiting

## Escopo

Este repositório consome APIs públicas e, em alguns casos, chaves de acesso para rate limiting ou autenticação. Questões de segurança incluem:

- exposição acidental de chaves
- bypass indevido de limites oficiais
- gravação indevida de dados sensíveis em logs
- dependências comprometidas ou desatualizadas
