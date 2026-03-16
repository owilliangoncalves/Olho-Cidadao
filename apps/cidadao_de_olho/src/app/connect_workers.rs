use loco_rs::{app::AppContext, bgworker::Queue, Result};

/// Conexão de workers assíncronos, hoje não utilizada pelo app.
pub(super) async fn connect_workers(_ctx: &AppContext, _queue: &Queue) -> Result<()> {
    Ok(())
}
