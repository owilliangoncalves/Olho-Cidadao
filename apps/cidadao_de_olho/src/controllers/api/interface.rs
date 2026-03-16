use axum::{debug_handler, response::Response};
use loco_rs::prelude::*;

use crate::services::citizen_eye::servico_compartilhado;

#[debug_handler]
/// Entrega a configuracao textual da interface publica.
pub(super) async fn interface() -> Result<Response> {
    let service = servico_compartilhado().map_err(|error| Error::string(&error.to_string()))?;
    format::json(service.interface_publica())
}
