//! DTOs públicos serializados para o frontend.
//!
//! Tudo aqui faz parte do contrato JSON exposto por `/api/snapshot`.

mod coverage_card;
mod feed_card;
mod hero_section;
mod ranking_item;
mod snapshot;
mod termo_glossario;
mod ui_payload;

pub use self::coverage_card::CoverageCard;
pub use self::feed_card::FeedCard;
pub use self::hero_section::{HeroSection, HighlightCard, MetricCard};
pub use self::ranking_item::{RankingGroups, RankingItem};
pub use self::snapshot::{Snapshot, SnapshotMeta};
pub use self::termo_glossario::TermoGlossario;
pub use self::ui_payload::UiPayload;
