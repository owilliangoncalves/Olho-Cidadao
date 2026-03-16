use axum::{
    debug_handler,
    response::{Html, IntoResponse, Response},
};
use loco_rs::prelude::*;

use super::load_index_html::load_index_html;

#[debug_handler]
/// Entrega o HTML inicial da aplicação.
pub(super) async fn index() -> Result<Response> {
    let html = load_index_html();
    Ok(Html(html).into_response())
}
