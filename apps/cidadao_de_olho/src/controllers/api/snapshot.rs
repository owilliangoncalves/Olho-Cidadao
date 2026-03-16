use axum::{debug_handler, extract::Query, response::Response};
use loco_rs::prelude::*;

use crate::services::citizen_eye::servico_compartilhado;

use super::snapshot_query::SnapshotQuery;

#[debug_handler]
/// Entrega o snapshot público consolidado consumido pelo frontend.
///
/// O cálculo roda em `spawn_blocking` porque envolve leitura de disco e
/// agregação síncrona de artefatos locais.
pub(super) async fn snapshot(Query(query): Query<SnapshotQuery>) -> Result<Response> {
    let refresh = query.refresh;
    let service = servico_compartilhado().map_err(|error| Error::string(&error.to_string()))?;
    let snapshot = tokio::task::spawn_blocking(move || service.snapshot(refresh))
        .await
        .map_err(|error| Error::string(&format!("falha ao aguardar snapshot: {error}")))?
        .map_err(|error| Error::string(&error.to_string()))?;

    format::json(snapshot)
}
