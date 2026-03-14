# Cidadão de Olho

Aplicacao publica do projeto, construida com `Loco.rs` no backend e uma camada `React + Vite + Tailwind + Radix UI` no frontend.

## Arquitetura

- `src/controllers/api.rs`
  Expõe os endpoints JSON do ambiente público.
- `src/controllers/site.rs`
  Entrega a interface web construída em `assets/static/ui/`.
- `src/services/citizen_eye.rs`
  Lê os artefatos do ETL e monta o snapshot público consumido pelo frontend.
- `src/config/citizen_data.rs`
  Carrega os caminhos e limites de leitura dos dados.
- `src/config/citizen_ui.rs`
  Carrega branding e textos exibidos na interface.
- `ui/`
  Workspace do frontend com React, Tailwind, Vite e Radix UI.

## Fluxo de dados

O fluxo principal do backend foi organizado em camadas com responsabilidades explícitas:

1. `src/services/citizen_eye/repositorio.rs`
   Lê os artefatos produzidos pelo ETL e normaliza Câmara, Senado e dimensão de fornecedores.
2. `src/services/citizen_eye/cache.rs`
   Mantém em memória o último snapshot válido, usando assinatura dos arquivos para invalidar o cache.
3. `src/services/citizen_eye/montador.rs`
   Consolida estatísticas, rankings, cards e metadados públicos.
4. `src/services/citizen_eye/modelos.rs`
   Define o contrato serializado entregue por `GET /api/snapshot`.
5. `src/services/citizen_eye.rs`
   Orquestra o fluxo inteiro, sem concentrar parsing ou agregação.

Essa separação existe para evitar acoplamento entre:
- formato físico dos arquivos;
- regras de agregação;
- contrato público da API;
- estratégia de cache.

## Configuracoes

As responsabilidades ficam separadas por arquivo:

- `config/development.yaml`, `config/test.yaml`, `config/production.yaml`
  Configuracoes de runtime do `Loco.rs`.
- `config/citizen_data.development.toml`, `config/citizen_data.test.toml`, `config/citizen_data.production.toml`
  Caminhos de entrada e limites de leitura dos dados públicos.
- `config/citizen_ui.toml`
  Textos, branding e copy da interface.
- `ui/.env.example`
  Configuracao da base da API consumida pelo frontend.

## Frontend

O frontend vive em `ui/` e gera o bundle final em `assets/static/ui/`.

### Instalar dependencias

```bash
npm install
```

### Gerar a interface publica

```bash
npm run build
```

### Rodar o frontend isolado em modo desenvolvimento

```bash
npm run dev
```

## Backend

Para iniciar o app `Loco.rs`:

```bash
cargo run -- start
```

Ou pela CLI principal do projeto:

```bash
uv run python main.py servir-Cidadão-de-olho
```

## Contrato da API

- `GET /api/health`
  Healthcheck simples da aplicacao.
- `GET /api/snapshot`
  Entrega o snapshot consolidado consumido pelo feed público.
- `GET /api/snapshot?refresh=1`
  Recalcula o snapshot ignorando o cache em memória.

## Validacao

Backend:

```bash
cargo test --manifest-path apps/Cidadão_de_olho/Cargo.toml
```

Frontend:

```bash
cd apps/Cidadão_de_olho/ui
npm run build
```
