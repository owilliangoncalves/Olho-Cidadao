//! Modelos internos normalizados do domínio.
//!
//! Estas structs não são o contrato da API. Elas existem para representar o
//! domínio de forma estável dentro do backend, desacoplando parsing dos
//! arquivos, agregação e serialização pública.

use std::collections::{BTreeSet, HashSet};

use super::modelos::FeedCard;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
/// Fontes públicas atualmente consolidadas pelo app.
pub(crate) enum FontePublica {
    Camara,
    Senado,
}

impl FontePublica {
    pub(crate) fn feed_label(self) -> &'static str {
        match self {
            Self::Camara => "Camara",
            Self::Senado => "Senado",
        }
    }

    pub(crate) fn display_label(self) -> &'static str {
        match self {
            Self::Camara => "Câmara",
            Self::Senado => "Senado",
        }
    }

    pub(crate) fn ranking_label(self) -> &'static str {
        self.feed_label()
    }

    pub(crate) fn coverage_focus(self) -> &'static str {
        match self {
            Self::Camara => "despesas parlamentares",
            Self::Senado => "reembolsos CEAPS",
        }
    }
}

#[derive(Clone, Debug)]
/// Registro normalizado de despesa pública, independente do arquivo de origem.
pub(crate) struct RegistroDespesa {
    pub source: FontePublica,
    pub sort_key: i64,
    pub amount_value: f64,
    pub year: i32,
    pub period: String,
    pub actor: String,
    pub actor_meta: String,
    pub actor_rank_key: String,
    pub supplier: String,
    pub supplier_doc: Option<String>,
    pub expense_type: String,
    pub tags: Vec<String>,
    pub uf: Option<String>,
}

#[derive(Clone, Debug, Default)]
/// Entradas já normalizadas que alimentam o montador de snapshot.
pub(crate) struct EntradasSnapshot {
    pub supplier_dimension_count: usize,
    pub records: Vec<RegistroDespesa>,
}

#[derive(Default)]
/// Estatísticas agregadas por fonte.
pub(crate) struct EstatisticasFonte {
    pub total_value: f64,
    pub records: usize,
    pub agents: HashSet<String>,
    pub suppliers: HashSet<String>,
    pub years: BTreeSet<i32>,
}

#[derive(Clone, Debug)]
/// Acumulador de ranking usado durante a montagem do snapshot.
pub(crate) struct FaixaRanking {
    pub label: String,
    pub total_value: f64,
    pub count: usize,
    pub sources: BTreeSet<String>,
    pub extra: Option<String>,
}

#[derive(Clone)]
/// Envelope intermediário para ordenar cards antes do corte final do feed.
pub(crate) struct EnvelopeFeed {
    pub sort_key: i64,
    pub amount_value: f64,
    pub card: FeedCard,
}

#[derive(Clone, Default)]
/// Maior despesa individual identificada no recorte atual.
pub(crate) struct MaiorRegistro {
    pub amount_value: f64,
    pub actor: String,
    pub supplier: String,
    pub source: String,
    pub period: String,
}
