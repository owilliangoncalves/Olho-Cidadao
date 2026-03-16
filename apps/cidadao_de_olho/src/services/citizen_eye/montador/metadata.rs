use chrono::{Local, SecondsFormat};

use crate::services::citizen_eye::{
    formatacao::{format_currency, share_of},
    modelos::{HeroSection, MetricCard, SnapshotMeta},
};

use super::{
    acumulador_snapshot::AcumuladorSnapshot,
    combined_stats::CombinedStats,
    helpers::{union_len, union_years},
    montador_snapshot::MontadorSnapshot,
};

impl MontadorSnapshot {
    /// Consolida estatísticas globais das diferentes fontes.
    pub(super) fn calculate_combined_stats(
        &self,
        accumulator: &AcumuladorSnapshot,
    ) -> CombinedStats {
        let total_value =
            accumulator.camara_stats.total_value + accumulator.senado_stats.total_value;
        let combined_agents = union_len(
            &accumulator.camara_stats.agents,
            &accumulator.senado_stats.agents,
        );
        let combined_suppliers = union_len(
            &accumulator.camara_stats.suppliers,
            &accumulator.senado_stats.suppliers,
        );
        let coverage_years = union_years(
            &accumulator.camara_stats.years,
            &accumulator.senado_stats.years,
        );

        CombinedStats {
            total_value,
            combined_agents,
            combined_suppliers,
            coverage_years,
        }
    }

    /// Identifica qual fonte de dados possui o maior volume financeiro.
    pub(super) fn identify_dominant_source(
        &self,
        accumulator: &AcumuladorSnapshot,
        total_visible: f64,
    ) -> (String, f64, f64) {
        if accumulator.camara_stats.total_value >= accumulator.senado_stats.total_value {
            (
                crate::services::citizen_eye::dominio::FontePublica::Camara
                    .display_label()
                    .to_string(),
                accumulator.camara_stats.total_value,
                share_of(total_visible, accumulator.camara_stats.total_value),
            )
        } else {
            (
                crate::services::citizen_eye::dominio::FontePublica::Senado
                    .display_label()
                    .to_string(),
                accumulator.senado_stats.total_value,
                share_of(total_visible, accumulator.senado_stats.total_value),
            )
        }
    }

    /// Monta os metadados do snapshot.
    pub(super) fn build_metadata(&self, coverage_years: &[i32]) -> SnapshotMeta {
        SnapshotMeta {
            generated_at: Local::now().to_rfc3339_opts(SecondsFormat::Secs, false),
            title: self.ui_config.branding.title.clone(),
            sources: vec!["camara".to_string(), "senado".to_string()],
            coverage_years: coverage_years.to_vec(),
            notes: self.ui_config.copy.methodology.clone(),
            ui: self.ui_publica(),
        }
    }

    /// Monta a seção principal (Hero) do snapshot.
    pub(super) fn build_hero_section(
        &self,
        stats: &CombinedStats,
        supplier_dimension_count: usize,
    ) -> HeroSection {
        HeroSection {
            eyebrow: self.ui_config.branding.eyebrow.clone(),
            headline: self.ui_config.branding.headline.clone(),
            subheadline: self.ui_config.branding.subheadline.clone(),
            metrics: vec![
                MetricCard {
                    label: "Gasto total monitorado".to_string(),
                    value: format_currency(stats.total_value),
                    detail: "Soma de todos os registros da Câmara e do Senado exibidos aqui."
                        .to_string(),
                    tone: "amber".to_string(),
                },
                MetricCard {
                    label: "Agentes públicos".to_string(),
                    value: stats.combined_agents.to_string(),
                    detail: "Total de deputados e senadores com gastos identificados.".to_string(),
                    tone: "cyan".to_string(),
                },
                MetricCard {
                    label: "Fornecedores".to_string(),
                    value: supplier_dimension_count
                        .max(stats.combined_suppliers)
                        .to_string(),
                    detail: "Empresas e pessoas que receberam pagamentos no período.".to_string(),
                    tone: "green".to_string(),
                },
                MetricCard {
                    label: "Período analisado".to_string(),
                    value: stats
                        .coverage_years
                        .iter()
                        .take(4)
                        .map(std::string::ToString::to_string)
                        .collect::<Vec<_>>()
                        .join(", "),
                    detail: "Anos com dados disponíveis para consulta nesta interface.".to_string(),
                    tone: "magenta".to_string(),
                },
            ],
        }
    }
}
