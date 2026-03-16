//! Configuração de branding e copy da interface pública.
//!
//! O frontend recebe parte importante dos textos pelo backend para evitar copy
//! hardcoded na camada React e para permitir ajustes editoriais sem tocar na
//! lógica de renderização.

mod branding_config;
mod citizen_ui_config;
mod copy_config;

pub use self::branding_config::BrandingConfig;
pub use self::citizen_ui_config::CitizenUiConfig;
pub use self::copy_config::CopyConfig;
