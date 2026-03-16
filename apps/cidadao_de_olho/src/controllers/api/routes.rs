use loco_rs::prelude::*;

use super::{health::health, interface::interface, snapshot::snapshot};

/// Registra as rotas públicas da API.
pub fn routes() -> Routes {
    Routes::new()
        .prefix("/api")
        .add("/health", get(health))
        .add("/interface", get(interface))
        .add("/snapshot", get(snapshot))
}
