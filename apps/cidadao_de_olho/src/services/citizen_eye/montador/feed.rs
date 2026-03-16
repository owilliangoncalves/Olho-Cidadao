use std::cmp::Ordering;

use crate::services::citizen_eye::{
    dominio::{FontePublica, RegistroDespesa},
    formatacao::format_currency,
    modelos::FeedCard,
};

use super::{acumulador_snapshot::AcumuladorSnapshot, montador_snapshot::MontadorSnapshot};

impl MontadorSnapshot {
    /// Prepara e ordena os cartões do feed por recência e valor.
    pub(super) fn prepare_feed_cards(&self, accumulator: &mut AcumuladorSnapshot) -> Vec<FeedCard> {
        accumulator.feed.sort_by(|left, right| {
            right.sort_key.cmp(&left.sort_key).then_with(|| {
                right
                    .amount_value
                    .partial_cmp(&left.amount_value)
                    .unwrap_or(Ordering::Equal)
            })
        });

        accumulator
            .feed
            .iter()
            .take(self.limits.max_feed_items)
            .map(|entry| entry.card.clone())
            .collect()
    }
}

pub(super) fn build_feed_card(record: &RegistroDespesa) -> FeedCard {
    let headline = match record.source {
        FontePublica::Camara => {
            format!("{} apareceu com nova despesa pública.", record.actor)
        }
        FontePublica::Senado => {
            format!("{} apareceu no radar de reembolsos.", record.actor)
        }
    };

    let body = match record.source {
        FontePublica::Camara => {
            let mut meta_parts = record.actor_meta.split(" • ");
            let party = meta_parts.next().unwrap_or("Sem partido");
            let uf = meta_parts.next().unwrap_or("BR");
            format!(
                "{} registrou {} com {}. Partido {}, UF {}.",
                record.actor,
                record.expense_type.to_lowercase(),
                record.supplier,
                party,
                uf
            )
        }
        FontePublica::Senado => {
            format!(
                "{} registrou {} com {}.",
                record.actor,
                record.expense_type.to_lowercase(),
                record.supplier
            )
        }
    };

    FeedCard {
        source: record.source.feed_label().to_string(),
        period: record.period.clone(),
        headline,
        body,
        actor: record.actor.clone(),
        actor_meta: record.actor_meta.clone(),
        supplier: record.supplier.clone(),
        supplier_doc: record.supplier_doc.clone(),
        amount: format_currency(record.amount_value),
        expense_type: record.expense_type.clone(),
        tags: record.tags.clone(),
    }
}
