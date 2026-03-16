//! Definição da aplicação `Loco.rs`.
//!
//! Aqui ficam o bootstrap, o registro de rotas e os pontos de extensão do
//! framework. O objetivo é manter esta camada como composição da app, e não
//! como lugar de regra de negócio.

mod app_name;
mod app_version;
mod boot;
mod connect_workers;
mod initializers;
mod register_tasks;
mod routes;

use async_trait::async_trait;
use loco_rs::{
    app::{AppContext, Hooks, Initializer},
    bgworker::Queue,
    boot::{BootResult, StartMode},
    config::Config,
    controller::AppRoutes,
    environment::Environment,
    task::Tasks,
    Result,
};

use self::{
    app_name::app_name, app_version::app_version, boot::boot, connect_workers::connect_workers,
    initializers::initializers, register_tasks::register_tasks, routes::routes,
};

/// Implementação principal do app `Olho Cidadão` para o `Loco.rs`.
pub struct App;

#[async_trait]
impl Hooks for App {
    fn app_name() -> &'static str {
        app_name()
    }

    fn app_version() -> String {
        app_version()
    }

    async fn boot(
        mode: StartMode,
        environment: &Environment,
        config: Config,
    ) -> Result<BootResult> {
        boot::<Self>(mode, environment, config).await
    }

    async fn initializers(ctx: &AppContext) -> Result<Vec<Box<dyn Initializer>>> {
        initializers(ctx).await
    }

    fn routes(ctx: &AppContext) -> AppRoutes {
        routes(ctx)
    }

    async fn connect_workers(ctx: &AppContext, queue: &Queue) -> Result<()> {
        connect_workers(ctx, queue).await
    }

    fn register_tasks(tasks: &mut Tasks) {
        register_tasks(tasks)
    }
}
