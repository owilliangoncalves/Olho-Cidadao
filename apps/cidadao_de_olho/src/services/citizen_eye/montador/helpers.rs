use std::collections::{BTreeSet, HashSet};

use crate::services::citizen_eye::{
    dominio::{EstatisticasFonte, FontePublica, MaiorRegistro},
    formatacao::format_currency,
    modelos::CoverageCard,
};

/// Serializa o resumo de cobertura de uma fonte para o contrato público.
pub(super) fn serialize_source_stats(
    source: FontePublica,
    stats: &EstatisticasFonte,
) -> CoverageCard {
    CoverageCard {
        source: source.display_label().to_string(),
        total: format_currency(stats.total_value),
        records: stats.records,
        agents: stats.agents.len(),
        suppliers: stats.suppliers.len(),
        focus: source.coverage_focus().to_string(),
    }
}

/// Atualiza o maior registro individual encontrado no recorte.
pub(super) fn update_highest_entry(
    highest_entry: &mut MaiorRegistro,
    value: f64,
    actor: &str,
    supplier: &str,
    source: &str,
    period: &str,
) {
    if value > highest_entry.amount_value {
        highest_entry.amount_value = value;
        highest_entry.actor = actor.to_string();
        highest_entry.supplier = supplier.to_string();
        highest_entry.source = source.to_string();
        highest_entry.period = period.to_string();
    }
}

/// Une anos de duas fontes e devolve a lista ordenada do mais recente ao mais antigo.
pub(super) fn union_years(left: &BTreeSet<i32>, right: &BTreeSet<i32>) -> Vec<i32> {
    let mut years = left.union(right).copied().collect::<Vec<_>>();
    years.sort_by(|a, b| b.cmp(a));
    years
}

/// Conta o total distinto da união entre dois conjuntos.
pub(super) fn union_len(left: &HashSet<String>, right: &HashSet<String>) -> usize {
    left.union(right).count()
}
