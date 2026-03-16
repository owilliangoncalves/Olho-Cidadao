use std::collections::HashMap;

use crate::services::citizen_eye::dominio::{
    EnvelopeFeed, EstatisticasFonte, FaixaRanking, FontePublica, MaiorRegistro, RegistroDespesa,
};

use super::{feed::build_feed_card, helpers::update_highest_entry, ranking::accumulate_rank};

#[derive(Default)]
pub(super) struct AcumuladorSnapshot {
    pub(super) camara_stats: EstatisticasFonte,
    pub(super) senado_stats: EstatisticasFonte,
    pub(super) supplier_rank: HashMap<String, FaixaRanking>,
    pub(super) agent_rank: HashMap<String, FaixaRanking>,
    pub(super) expense_rank: HashMap<String, FaixaRanking>,
    pub(super) uf_rank: HashMap<String, FaixaRanking>,
    pub(super) feed: Vec<EnvelopeFeed>,
    pub(super) highest_entry: MaiorRegistro,
}

impl AcumuladorSnapshot {
    /// Incorpora um registro normalizado às estruturas agregadas do snapshot.
    pub(super) fn ingest(&mut self, record: &RegistroDespesa) {
        let stats = match record.source {
            FontePublica::Camara => &mut self.camara_stats,
            FontePublica::Senado => &mut self.senado_stats,
        };

        stats.total_value += record.amount_value;
        stats.records += 1;
        stats.agents.insert(record.actor.clone());
        if let Some(doc) = &record.supplier_doc {
            stats.suppliers.insert(doc.clone());
        }
        if record.year > 0 {
            stats.years.insert(record.year);
        }

        accumulate_rank(
            &mut self.supplier_rank,
            record
                .supplier_doc
                .clone()
                .unwrap_or_else(|| record.supplier.clone()),
            record.supplier.clone(),
            record.amount_value,
            record.source.ranking_label(),
            None,
        );
        accumulate_rank(
            &mut self.agent_rank,
            record.actor_rank_key.clone(),
            record.actor.clone(),
            record.amount_value,
            record.source.ranking_label(),
            Some(record.actor_meta.clone()),
        );
        accumulate_rank(
            &mut self.expense_rank,
            record.expense_type.clone(),
            record.expense_type.clone(),
            record.amount_value,
            record.source.ranking_label(),
            None,
        );

        if let Some(uf) = &record.uf {
            accumulate_rank(
                &mut self.uf_rank,
                uf.clone(),
                uf.clone(),
                record.amount_value,
                record.source.ranking_label(),
                None,
            );
        }

        update_highest_entry(
            &mut self.highest_entry,
            record.amount_value,
            &record.actor,
            &record.supplier,
            record.source.display_label(),
            &record.period,
        );

        self.feed.push(EnvelopeFeed {
            sort_key: record.sort_key,
            amount_value: record.amount_value,
            card: build_feed_card(record),
        });
    }
}
