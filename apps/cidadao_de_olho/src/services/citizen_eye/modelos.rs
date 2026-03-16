//! DTOs públicos serializados para o frontend.
//!
//! Tudo aqui faz parte do contrato JSON exposto por `/api/snapshot`.

use serde::Serialize;

use crate::config::{
    citizen_ui::CopyConfig, glossario::TermoGlossarioConfig, textos::TextosConfig,
};

#[derive(Clone, Debug, Serialize)]
/// Snapshot completo consumido pela interface pública.
pub struct Snapshot {
    pub meta: SnapshotMeta,
    pub hero: HeroSection,
    pub highlights: Vec<HighlightCard>,
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

#[derive(Clone, Debug, Serialize)]
/// Textos de interface enviados pelo backend para evitar copy hardcoded no frontend.
pub struct UiPayload {
    pub eyebrow: String,
    pub refresh_label: String,
    pub feed_title: String,
    pub feed_subtitle: String,
    pub search_label: String,
    pub search_placeholder: String,
    pub guide_title: String,
    pub guide_body: String,
    pub methodology_title: String,
    pub empty_feed_message: String,
    pub coverage_title: String,
    pub highlights_title: String,
    pub suppliers_title: String,
    pub agents_title: String,
    pub expenses_title: String,
    pub textos: TextosConfig,
}

impl UiPayload {
    /// Converte a configuração de copy em payload pronto para a interface.
    pub fn from_configuracoes(
        copy: &CopyConfig,
        refresh_label: &str,
        textos: &TextosConfig,
    ) -> Self {
        Self {
            eyebrow: "Feed civico".to_string(),
            refresh_label: refresh_label.to_string(),
            feed_title: copy.feed_title.clone(),
            feed_subtitle: copy.feed_subtitle.clone(),
            search_label: copy.search_label.clone(),
            search_placeholder: copy.search_placeholder.clone(),
            guide_title: copy.guide_title.clone(),
            guide_body: copy.guide_body.clone(),
            methodology_title: copy.methodology_title.clone(),
            empty_feed_message: copy.empty_feed_message.clone(),
            coverage_title: copy.coverage_title.clone(),
            highlights_title: copy.highlights_title.clone(),
            suppliers_title: copy.suppliers_title.clone(),
            agents_title: copy.agents_title.clone(),
            expenses_title: copy.expenses_title.clone(),
            textos: textos.clone(),
        }
    }
}

#[derive(Clone, Debug, Serialize)]
/// Bloco principal de abertura da interface.
pub struct HeroSection {
    pub eyebrow: String,
    pub headline: String,
    pub subheadline: String,
    pub metrics: Vec<MetricCard>,
}

#[derive(Clone, Debug, Serialize)]
/// Métrica resumida exibida no hero da aplicação.
pub struct MetricCard {
    pub label: String,
    pub value: String,
    pub detail: String,
    pub tone: String,
}

#[derive(Clone, Debug, Serialize)]
/// Card de destaque rápido exibido no topo da experiência.
pub struct HighlightCard {
    pub title: String,
    pub value: String,
    pub detail: String,
}

#[derive(Clone, Debug, Serialize)]
/// Resumo da cobertura detectada por fonte pública.
pub struct CoverageCard {
    pub source: String,
    pub total: String,
    pub records: usize,
    pub agents: usize,
    pub suppliers: usize,
    pub focus: String,
}

#[derive(Clone, Debug, Serialize)]
/// Agrupamento dos rankings usados na navegação principal da interface.
pub struct RankingGroups {
    pub fornecedores: Vec<RankingItem>,
    pub agentes: Vec<RankingItem>,
    pub tipos_despesa: Vec<RankingItem>,
    pub ufs: Vec<RankingItem>,
}

#[derive(Clone, Debug, Serialize)]
/// Termo do glossario acessivel exibido na interface.
pub struct TermoGlossario {
    pub termo: String,
    pub grupo: String,
    pub definicao: String,
    pub contexto: String,
    pub relacionados: Vec<String>,
}

impl TermoGlossario {
    /// Converte a configuracao editorial em payload publico.
    pub fn from_config(config: &TermoGlossarioConfig) -> Self {
        Self {
            termo: config.termo.clone(),
            grupo: config.grupo.clone(),
            definicao: config.definicao.clone(),
            contexto: config.contexto.clone(),
            relacionados: config.relacionados.clone(),
        }
    }
}

#[derive(Clone, Debug, Serialize)]
/// Item unitário de ranking.
pub struct RankingItem {
    pub label: String,
    pub value: String,
    pub extra: Option<String>,
    pub sources: Vec<String>,
    pub share: f64,
}

#[derive(Clone, Debug, Serialize)]
/// Card unitário do feed cívico.
pub struct FeedCard {
    pub source: String,
    pub period: String,
    pub headline: String,
    pub body: String,
    pub actor: String,
    pub actor_meta: String,
    pub supplier: String,
    pub supplier_doc: Option<String>,
    pub amount: String,
    pub expense_type: String,
    pub tags: Vec<String>,
}
