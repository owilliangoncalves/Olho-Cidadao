use axum::{debug_handler, response::Response};
use loco_rs::prelude::*;

#[debug_handler]
/// Healthcheck simples para monitoração da aplicação.
pub(super) async fn health() -> Result<Response> {
    format::json(serde_json::json!({
        "status": "ok",
        "service": "cidadao_de_olho",
    }))
}
