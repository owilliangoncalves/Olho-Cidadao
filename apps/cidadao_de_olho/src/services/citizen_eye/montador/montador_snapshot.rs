use crate::config::{
    citizen_data::CitizenDataLimits, citizen_ui::CitizenUiConfig, glossario::GlossarioConfig,
    textos::TextosConfig,
};

use super::acumulador_snapshot::AcumuladorSnapshot;
use crate::services::citizen_eye::{
    dominio::EntradasSnapshot,
    modelos::{Snapshot, UiPayload},
};

#[derive(Clone)]
/// Monta o contrato final consumido pelo frontend.
pub(crate) struct MontadorSnapshot {
    pub(super) limits: CitizenDataLimits,
    pub(super) ui_config: CitizenUiConfig,
    pub(super) glossario_config: GlossarioConfig,
    pub(super) textos_config: TextosConfig,
}

impl MontadorSnapshot {
    /// Cria o montador com os limites de exposição e a copy da interface.
    pub(crate) fn new(
        limits: CitizenDataLimits,
        ui_config: CitizenUiConfig,
        glossario_config: GlossarioConfig,
        textos_config: TextosConfig,
    ) -> Self {
        Self {
            limits,
            ui_config,
            glossario_config,
            textos_config,
        }
    }

    /// Retorna o payload de interface independente do snapshot de dados.
    pub(crate) fn ui_publica(&self) -> UiPayload {
        UiPayload::from_configuracoes(
            &self.ui_config.copy,
            &self.ui_config.branding.refresh_label,
            &self.textos_config,
        )
    }

    /// Constrói o snapshot completo a partir das entradas já normalizadas.
    pub(crate) fn build(&self, inputs: EntradasSnapshot) -> Snapshot {
        let mut accumulator = AcumuladorSnapshot::default();
        for record in &inputs.records {
            accumulator.ingest(record);
        }

        let feed_cards = self.prepare_feed_cards(&mut accumulator);
        let combined_stats = self.calculate_combined_stats(&accumulator);
        let rankings = self.generate_all_rankings(&accumulator);
        let dominant_source =
            self.identify_dominant_source(&accumulator, combined_stats.total_value);

        Snapshot {
            meta: self.build_metadata(&combined_stats.coverage_years),
            hero: self.build_hero_section(&combined_stats, inputs.supplier_dimension_count),
            highlights: self.build_highlights(&accumulator, &rankings, &dominant_source),
            coverage: self.build_coverage_section(&accumulator),
            rankings: rankings.into_groups(),
            glossario: self.build_glossario(),
            feed: feed_cards,
        }
    }
}
