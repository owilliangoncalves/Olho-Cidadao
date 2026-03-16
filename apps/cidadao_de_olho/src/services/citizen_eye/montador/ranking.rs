use std::{
    cmp::Ordering,
    collections::{BTreeSet, HashMap},
};

use crate::services::citizen_eye::{
    dominio::FaixaRanking,
    formatacao::{format_currency, share_of},
    modelos::RankingItem,
};

use super::{
    acumulador_snapshot::AcumuladorSnapshot, montador_snapshot::MontadorSnapshot,
    snapshot_rankings::SnapshotRankings,
};

impl MontadorSnapshot {
    /// Gera todos os rankings (fornecedores, agentes, despesas, UFs).
    pub(super) fn generate_all_rankings(
        &self,
        accumulator: &AcumuladorSnapshot,
    ) -> SnapshotRankings {
        SnapshotRankings {
            suppliers: top_currency_rankings(
                &accumulator.supplier_rank,
                self.limits.max_ranking_items,
            ),
            agents: top_currency_rankings(&accumulator.agent_rank, self.limits.max_ranking_items),
            expenses: top_currency_rankings(
                &accumulator.expense_rank,
                self.limits.max_ranking_items,
            ),
            ufs: top_currency_rankings(&accumulator.uf_rank, self.limits.max_ranking_items),
        }
    }
}

/// Ordena e serializa um mapa de agregações em itens consumíveis pelo frontend.
pub(super) fn top_currency_rankings(
    rank_map: &HashMap<String, FaixaRanking>,
    limit: usize,
) -> Vec<RankingItem> {
    let mut entries = rank_map.values().cloned().collect::<Vec<_>>();
    entries.sort_by(|left, right| {
        right
            .total_value
            .partial_cmp(&left.total_value)
            .unwrap_or(Ordering::Equal)
            .then_with(|| left.label.cmp(&right.label))
    });

    let total = entries.iter().map(|entry| entry.total_value).sum::<f64>();
    entries
        .into_iter()
        .take(limit)
        .map(|entry| RankingItem {
            label: entry.label,
            value: format_currency(entry.total_value),
            extra: entry
                .extra
                .or_else(|| Some(format!("{} registros", entry.count))),
            sources: entry.sources.into_iter().collect(),
            share: (share_of(total, entry.total_value) * 1000.0).round() / 10.0,
        })
        .collect()
}

/// Acumula valor e ocorrência em uma faixa de ranking.
pub(super) fn accumulate_rank(
    rank_map: &mut HashMap<String, FaixaRanking>,
    key: String,
    label: String,
    value: f64,
    source: &str,
    extra: Option<String>,
) {
    let bucket = rank_map.entry(key).or_insert_with(|| FaixaRanking {
        label,
        total_value: 0.0,
        count: 0,
        sources: BTreeSet::new(),
        extra,
    });
    bucket.total_value += value;
    bucket.count += 1;
    bucket.sources.insert(source.to_string());
}
