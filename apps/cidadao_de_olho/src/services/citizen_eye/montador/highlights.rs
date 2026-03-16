use crate::services::citizen_eye::{
    formatacao::{format_currency, format_share},
    modelos::{HighlightCard, RankingItem},
};

use super::{
    acumulador_snapshot::AcumuladorSnapshot, montador_snapshot::MontadorSnapshot,
    snapshot_rankings::SnapshotRankings,
};

impl MontadorSnapshot {
    /// Monta os cartões de destaque (highlights).
    pub(super) fn build_highlights(
        &self,
        accumulator: &AcumuladorSnapshot,
        rankings: &SnapshotRankings,
        dominant_source: &(String, f64, f64),
    ) -> Vec<HighlightCard> {
        vec![
            build_ranking_highlight(
                "Principal fornecedor",
                rankings.suppliers.first(),
                "em pagamentos identificados.",
                "Nenhum fornecedor encontrado no recorte atual.",
            ),
            build_ranking_highlight(
                "Agente com maior gasto",
                rankings.agents.first(),
                "em despesas registradas.",
                "Nenhum agente público identificado.",
            ),
            HighlightCard {
                title: "Maior gasto individual".to_string(),
                value: if accumulator.highest_entry.amount_value > 0.0 {
                    format_currency(accumulator.highest_entry.amount_value)
                } else {
                    "Sem dados".to_string()
                },
                detail: if accumulator.highest_entry.amount_value > 0.0 {
                    format!(
                        "{} pagou {} em {} ({})",
                        accumulator.highest_entry.actor,
                        accumulator.highest_entry.supplier,
                        accumulator.highest_entry.period,
                        accumulator.highest_entry.source
                    )
                } else {
                    "Nenhum registro individual encontrado.".to_string()
                },
            },
            HighlightCard {
                title: "Fonte predominante".to_string(),
                value: dominant_source.0.clone(),
                detail: format!(
                    "{} do volume total, com {}.",
                    format_share(dominant_source.2),
                    format_currency(dominant_source.1)
                ),
            },
        ]
    }
}

fn build_ranking_highlight(
    title: &str,
    item: Option<&RankingItem>,
    detail_suffix: &str,
    empty_detail: &str,
) -> HighlightCard {
    let (value, detail) = match item {
        Some(item) => (
            item.label.clone(),
            format!("{} {}", item.value, detail_suffix),
        ),
        None => ("Sem dados".to_string(), empty_detail.to_string()),
    };

    HighlightCard {
        title: title.to_string(),
        value,
        detail,
    }
}
