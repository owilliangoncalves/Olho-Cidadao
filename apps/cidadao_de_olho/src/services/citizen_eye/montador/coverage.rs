use crate::services::citizen_eye::{dominio::FontePublica, modelos::CoverageCard};

use super::{
    acumulador_snapshot::AcumuladorSnapshot, helpers::serialize_source_stats,
    montador_snapshot::MontadorSnapshot,
};

impl MontadorSnapshot {
    /// Monta a seção de cobertura por fonte.
    pub(super) fn build_coverage_section(
        &self,
        accumulator: &AcumuladorSnapshot,
    ) -> Vec<CoverageCard> {
        vec![
            serialize_source_stats(FontePublica::Camara, &accumulator.camara_stats),
            serialize_source_stats(FontePublica::Senado, &accumulator.senado_stats),
        ]
    }
}
