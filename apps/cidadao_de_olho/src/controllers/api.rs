//! Endpoints JSON públicos do `Cidadão de Olho`.
//!
//! Esta camada mantém o controller fino: recebe a requisição HTTP, delega ao
//! serviço de domínio e serializa o contrato final como JSON.

use axum::{debug_handler, extract::Query, response::Response};
use loco_rs::prelude::*;
use serde::Deserialize;

use crate::services::citizen_eye::servico_compartilhado;

#[derive(Debug, Default, Deserialize)]
/// Query string aceita pelo endpoint de snapshot.
struct SnapshotQuery {
    refresh: Option<bool>,
}

#[debug_handler]
/// Healthcheck simples para monitoração da aplicação.
async fn health() -> Result<Response> {
    format::json(serde_json::json!({
        "status": "ok",
        "service": "cidadao_de_olho",
    }))
}

#[debug_handler]
/// Entrega o snapshot público consolidado consumido pelo frontend.
///
/// O cálculo roda em `spawn_blocking` porque envolve leitura de disco e
/// agregação síncrona de artefatos locais.
async fn snapshot(Query(query): Query<SnapshotQuery>) -> Result<Response> {
    let refresh = query.refresh.unwrap_or(false);
    let service = servico_compartilhado().clone();
    let snapshot = tokio::task::spawn_blocking(move || service.snapshot(refresh))
        .await
        .map_err(|error| Error::string(&format!("falha ao aguardar snapshot: {error}")))?
        .map_err(|error| Error::string(&error.to_string()))?;

    format::json(snapshot)
}

/// Registra as rotas públicas da API.
pub fn routes() -> Routes {
    Routes::new()
        .prefix("/api")
        .add("/health", get(health))
        .add("/snapshot", get(snapshot))
}
