use serde::Serialize;

use super::{CoverageCard, FeedCard, HeroSection, RankingGroups, TermoGlossario, UiPayload};

#[derive(Clone, Debug, Serialize)]
/// Snapshot completo consumido pela interface pública.
pub struct Snapshot {
    pub meta: SnapshotMeta,
    pub hero: HeroSection,
    pub highlights: Vec<super::hero_section::HighlightCard>,
    pub coverage: Vec<CoverageCard>,
    pub rankings: RankingGroups,
    pub glossario: Vec<TermoGlossario>,
    pub feed: Vec<FeedCard>,
}

#[derive(Clone, Debug, Serialize)]
/// Metadados globais do snapshot.
pub struct SnapshotMeta {
    pub generated_at: String,
    pub title: String,
    pub sources: Vec<String>,
    pub coverage_years: Vec<i32>,
    pub notes: Vec<String>,
    pub ui: UiPayload,
}
