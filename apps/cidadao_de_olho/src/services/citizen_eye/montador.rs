//! Montagem do snapshot público a partir de entradas normalizadas.
//!
//! Este módulo concentra a lógica de agregação, ordenação e montagem dos DTOs
//! expostos pela API. Ele não lê arquivos diretamente e não conhece cache.

use std::{
    cmp::Ordering,
    collections::{BTreeSet, HashMap, HashSet},
};

use chrono::{Local, SecondsFormat};

use crate::config::{citizen_data::CitizenDataLimits, citizen_ui::CitizenUiConfig};

use super::{
    dominio::{
        EntradasSnapshot, EnvelopeFeed, EstatisticasFonte, FaixaRanking, FontePublica,
        MaiorRegistro, RegistroDespesa,
    },
    formatacao::{format_currency, format_share, share_of},
    modelos::{
        CoverageCard, FeedCard, HeroSection, HighlightCard, MetricCard, RankingGroups, RankingItem,
        Snapshot, SnapshotMeta, UiPayload,
    },
};

#[derive(Copy, Clone)]
enum RankingMetric {
    Currency,
}

#[derive(Clone)]
/// Monta o contrato final consumido pelo frontend.
pub(crate) struct MontadorSnapshot {
    limits: CitizenDataLimits,
    ui_config: CitizenUiConfig,
}

#[derive(Default)]
struct AcumuladorSnapshot {
    camara_stats: EstatisticasFonte,
    senado_stats: EstatisticasFonte,
    supplier_rank: HashMap<String, FaixaRanking>,
    agent_rank: HashMap<String, FaixaRanking>,
    expense_rank: HashMap<String, FaixaRanking>,
    uf_rank: HashMap<String, FaixaRanking>,
    feed: Vec<EnvelopeFeed>,
    highest_entry: MaiorRegistro,
}

impl MontadorSnapshot {
    /// Cria o montador com os limites de exposição e a copy da interface.
    pub(crate) fn new(limits: CitizenDataLimits, ui_config: CitizenUiConfig) -> Self {
        Self { limits, ui_config }
    }

    /// Constrói o snapshot completo a partir das entradas já normalizadas.
    pub(crate) fn build(&self, inputs: EntradasSnapshot) -> Snapshot {
        let mut accumulator = AcumuladorSnapshot::default();
        for record in &inputs.records {
            accumulator.ingest(record);
        }

        // O feed é ordenado por recência e, em empate, pelo maior valor.
        // Isso mantém a timeline útil sem perder a noção de intensidade.
        accumulator.feed.sort_by(|left, right| {
            right.sort_key.cmp(&left.sort_key).then_with(|| {
                right
                    .amount_value
                    .partial_cmp(&left.amount_value)
                    .unwrap_or(Ordering::Equal)
            })
        });

        let feed_cards = accumulator
            .feed
            .into_iter()
            .take(self.limits.max_feed_items)
            .map(|entry| entry.card)
            .collect::<Vec<_>>();

        let total_visible =
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

        let top_suppliers = top_rankings(
            &accumulator.supplier_rank,
            self.limits.max_ranking_items,
            RankingMetric::Currency,
        );
        let top_agents = top_rankings(
            &accumulator.agent_rank,
            self.limits.max_ranking_items,
            RankingMetric::Currency,
        );
        let top_expenses = top_rankings(
            &accumulator.expense_rank,
            self.limits.max_ranking_items,
            RankingMetric::Currency,
        );
        let top_ufs = top_rankings(
            &accumulator.uf_rank,
            self.limits.max_ranking_items,
            RankingMetric::Currency,
        );

        // A fonte dominante é definida pelo maior volume financeiro visível
        // no recorte atual. Esse destaque aparece na área de highlights.
        let dominant_source =
            if accumulator.camara_stats.total_value >= accumulator.senado_stats.total_value {
                (
                    FontePublica::Camara.display_label().to_string(),
                    accumulator.camara_stats.total_value,
                    share_of(total_visible, accumulator.camara_stats.total_value),
                )
            } else {
                (
                    FontePublica::Senado.display_label().to_string(),
                    accumulator.senado_stats.total_value,
                    share_of(total_visible, accumulator.senado_stats.total_value),
                )
            };

        Snapshot {
            meta: SnapshotMeta {
                generated_at: Local::now().to_rfc3339_opts(SecondsFormat::Secs, false),
                title: self.ui_config.branding.title.clone(),
                sources: vec!["camara".to_string(), "senado".to_string()],
                coverage_years: coverage_years.clone(),
                notes: self.ui_config.copy.methodology.clone(),
                ui: UiPayload::from_copy(
                    &self.ui_config.copy,
                    &self.ui_config.branding.refresh_label,
                ),
            },
            hero: HeroSection {
                eyebrow: self.ui_config.branding.eyebrow.clone(),
                headline: self.ui_config.branding.headline.clone(),
                subheadline: self.ui_config.branding.subheadline.clone(),
                metrics: vec![
                    MetricCard {
                        label: "Valor consolidado visivel".to_string(),
                        value: format_currency(total_visible),
                        detail: "Câmara e Senado nos artefatos já extraídos pelo ETL.".to_string(),
                        tone: "amber".to_string(),
                    },
                    MetricCard {
                        label: "Agentes publicos mapeados".to_string(),
                        value: combined_agents.to_string(),
                        detail: "Deputados e senadores com ocorrência nas bases lidas.".to_string(),
                        tone: "cyan".to_string(),
                    },
                    MetricCard {
                        label: "Fornecedores no radar".to_string(),
                        value: inputs
                            .supplier_dimension_count
                            .max(combined_suppliers)
                            .to_string(),
                        detail: "Documentos normalizados reunidos na dimensão pública.".to_string(),
                        tone: "green".to_string(),
                    },
                    MetricCard {
                        label: "Anos cobertos".to_string(),
                        value: coverage_years
                            .iter()
                            .take(4)
                            .map(std::string::ToString::to_string)
                            .collect::<Vec<_>>()
                            .join(", "),
                        detail: "O recorte temporal é detectado automaticamente pelos arquivos."
                            .to_string(),
                        tone: "magenta".to_string(),
                    },
                ],
            },
            highlights: vec![
                HighlightCard {
                    title: "Maior fornecedor mapeado".to_string(),
                    value: top_suppliers
                        .first()
                        .map(|item| item.label.clone())
                        .unwrap_or_else(|| "Sem dados".to_string()),
                    detail: top_suppliers
                        .first()
                        .map(|item| format!("{} nos registros visíveis.", item.value))
                        .unwrap_or_else(|| {
                            "Ainda não há valor consolidado disponível.".to_string()
                        }),
                },
                HighlightCard {
                    title: "Agente com maior volume".to_string(),
                    value: top_agents
                        .first()
                        .map(|item| item.label.clone())
                        .unwrap_or_else(|| "Sem dados".to_string()),
                    detail: top_agents
                        .first()
                        .map(|item| format!("{} somados nas despesas monitoradas.", item.value))
                        .unwrap_or_else(|| "Sem liderança definida nas bases lidas.".to_string()),
                },
                HighlightCard {
                    title: "Maior registro individual".to_string(),
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
                        "Nenhum registro individual foi identificado nas fontes lidas.".to_string()
                    },
                },
                HighlightCard {
                    title: "Fonte dominante no recorte".to_string(),
                    value: dominant_source.0,
                    detail: format!(
                        "{} do total visível, com {}.",
                        format_share(dominant_source.2),
                        format_currency(dominant_source.1)
                    ),
                },
            ],
            coverage: vec![
                serialize_source_stats(FontePublica::Camara, &accumulator.camara_stats),
                serialize_source_stats(FontePublica::Senado, &accumulator.senado_stats),
            ],
            rankings: RankingGroups {
                fornecedores: top_suppliers,
                agentes: top_agents,
                tipos_despesa: top_expenses,
                ufs: top_ufs,
            },
            feed: feed_cards,
        }
    }
}

impl AcumuladorSnapshot {
    /// Incorpora um registro normalizado às estruturas agregadas do snapshot.
    fn ingest(&mut self, record: &RegistroDespesa) {
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

fn build_feed_card(record: &RegistroDespesa) -> FeedCard {
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

/// Serializa o resumo de cobertura de uma fonte para o contrato público.
fn serialize_source_stats(source: FontePublica, stats: &EstatisticasFonte) -> CoverageCard {
    CoverageCard {
        source: source.display_label().to_string(),
        total: format_currency(stats.total_value),
        records: stats.records,
        agents: stats.agents.len(),
        suppliers: stats.suppliers.len(),
        focus: source.coverage_focus().to_string(),
    }
}

/// Ordena e serializa um mapa de agregações em itens consumíveis pelo frontend.
fn top_rankings(
    rank_map: &HashMap<String, FaixaRanking>,
    limit: usize,
    metric: RankingMetric,
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
            value: match metric {
                RankingMetric::Currency => format_currency(entry.total_value),
            },
            extra: entry
                .extra
                .or_else(|| Some(format!("{} registros", entry.count))),
            sources: entry.sources.into_iter().collect(),
            share: (share_of(total, entry.total_value) * 1000.0).round() / 10.0,
        })
        .collect()
}

/// Acumula valor e ocorrência em uma faixa de ranking.
fn accumulate_rank(
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

/// Atualiza o maior registro individual encontrado no recorte.
fn update_highest_entry(
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
fn union_years(left: &BTreeSet<i32>, right: &BTreeSet<i32>) -> Vec<i32> {
    let mut years = left.union(right).copied().collect::<Vec<_>>();
    years.sort_by(|a, b| b.cmp(a));
    years
}

/// Conta o total distinto da união entre dois conjuntos.
fn union_len(left: &HashSet<String>, right: &HashSet<String>) -> usize {
    left.union(right).count()
}
