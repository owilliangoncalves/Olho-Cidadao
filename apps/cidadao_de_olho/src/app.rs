//! Definição da aplicação `Loco.rs`.
//!
//! Aqui ficam o bootstrap, o registro de rotas e os pontos de extensão do
//! framework. O objetivo é manter esta camada como composição da app, e não
//! como lugar de regra de negócio.

use async_trait::async_trait;
use loco_rs::{
    app::{AppContext, Hooks, Initializer},
    bgworker::Queue,
    boot::{create_app, BootResult, StartMode},
    config::Config,
    controller::AppRoutes,
    environment::Environment,
    task::Tasks,
    Result,
};

use crate::controllers;

/// Implementação principal do app `Olho Cidadão` para o `Loco.rs`.
pub struct App;
#[async_trait]
impl Hooks for App {
    /// Nome canônico da aplicação.
    fn app_name() -> &'static str {
        env!("CARGO_CRATE_NAME")
    }

    /// Versão exposta pela aplicação, enriquecida com SHA quando disponível.
    fn app_version() -> String {
        format!(
            "{} ({})",
            env!("CARGO_PKG_VERSION"),
            option_env!("BUILD_SHA")
                .or(option_env!("GITHUB_SHA"))
                .unwrap_or("dev")
        )
    }

    async fn boot(
        mode: StartMode,
        environment: &Environment,
        config: Config,
    ) -> Result<BootResult> {
        create_app::<Self>(mode, environment, config).await
    }

    /// Inicializadores extras do app.
    async fn initializers(_ctx: &AppContext) -> Result<Vec<Box<dyn Initializer>>> {
        Ok(vec![])
    }

    /// Rotas registradas pela aplicação.
    fn routes(_ctx: &AppContext) -> AppRoutes {
        AppRoutes::with_default_routes() // controller routes below
            .add_route(controllers::site::routes())
            .add_route(controllers::api::routes())
    }

    /// Conexão de workers assíncronos, hoje não utilizada pelo app.
    async fn connect_workers(_ctx: &AppContext, _queue: &Queue) -> Result<()> {
        Ok(())
    }

    #[allow(unused_variables)]
    /// Registro de tarefas do framework, mantido por compatibilidade com o scaffold.
    fn register_tasks(tasks: &mut Tasks) {
        // tasks-inject (do not remove)
    }
}
