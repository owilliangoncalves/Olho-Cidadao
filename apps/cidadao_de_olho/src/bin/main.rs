//! Ponto de entrada do binário `Loco.rs` do `Olho Cidadão`.
//!
//! Este binário apenas delega ao bootstrap padrão do framework, mantendo a
//! inicialização centralizada em `src/app.rs`.

use cidadao_de_olho::app::App;
use loco_rs::cli;

/// Inicializa a CLI do `Loco.rs` usando a aplicação deste workspace.
#[tokio::main]
async fn main() -> loco_rs::Result<()> {
    cli::main::<App>().await
}
