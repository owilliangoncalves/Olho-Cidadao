//! Configuracao central de textos renderizados na interface publica.
//!
//! Cada secao do TOML representa uma pagina ou uma area compartilhada da
//! experiencia, evitando copy hardcoded na camada React.

mod textos_barra_superior;
mod textos_cobertura;
mod textos_compartilhados;
mod textos_config;
mod textos_estados;
mod textos_feed;
mod textos_glossario;
mod textos_rankings;
mod textos_visao_geral;

pub use self::textos_barra_superior::TextosBarraSuperior;
pub use self::textos_cobertura::TextosCobertura;
pub use self::textos_compartilhados::TextosCompartilhados;
pub use self::textos_config::TextosConfig;
pub use self::textos_estados::TextosEstados;
pub use self::textos_feed::TextosFeed;
pub use self::textos_glossario::TextosGlossario;
pub use self::textos_rankings::TextosRankings;
pub use self::textos_visao_geral::TextosVisaoGeral;
