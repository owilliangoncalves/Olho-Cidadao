use loco_rs::{app::AppContext, controller::AppRoutes};

use crate::controllers;

/// Rotas registradas pela aplicação.
pub(super) fn routes(_ctx: &AppContext) -> AppRoutes {
    AppRoutes::with_default_routes()
        .add_route(controllers::site::routes())
        .add_route(controllers::api::routes())
}
