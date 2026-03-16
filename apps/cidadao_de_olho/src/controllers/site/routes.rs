use loco_rs::prelude::*;

use super::index::index;

/// Registra a rota raiz da interface web.
pub fn routes() -> Routes {
    Routes::new().add("/", get(index))
}
