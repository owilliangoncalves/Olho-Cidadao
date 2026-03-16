use loco_rs::{
    boot::{create_app, BootResult, StartMode},
    config::Config,
    environment::Environment,
    Result,
};

pub(super) async fn boot<T>(
    mode: StartMode,
    environment: &Environment,
    config: Config,
) -> Result<BootResult>
where
    T: loco_rs::app::Hooks,
{
    create_app::<T>(mode, environment, config).await
}
