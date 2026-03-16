//! Orquestracao do snapshot publico do `Olho Cidadão`.
//!
//! Este módulo expõe a fachada da feature. A responsabilidade aqui é pequena
//! por design: carregar configuracoes, delegar leitura dos artefatos ao
//! repositorio, reaproveitar o cache em memoria e pedir ao montador que
//! produza o contrato JSON consumido pelo frontend.

mod cache;
mod dominio;
mod formatacao;
mod modelos;
mod montador;
mod repositorio;
mod servico;
mod singleton;

pub use self::modelos::{
    CoverageCard, FeedCard, HeroSection, HighlightCard, MetricCard, RankingGroups, RankingItem,
    Snapshot, SnapshotMeta, TermoGlossario, UiPayload,
};
pub use self::servico::ServicoCidadaoDeOlho;
pub use self::singleton::servico_compartilhado;
