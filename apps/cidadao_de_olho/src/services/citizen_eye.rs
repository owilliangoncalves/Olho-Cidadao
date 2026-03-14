//! Orquestracao do snapshot publico do `Cidadão de Olho`.
//!
//! Este módulo expõe a fachada da feature. A responsabilidade aqui é pequena
//! por design: carregar configuracoes, delegar leitura dos artefatos ao
//! repositorio, reaproveitar o cache em memoria e pedir ao montador que
//! produza o contrato JSON consumido pelo frontend.

mod cache;
mod dominio;
mod formatacao;
mod modelos;
mod montador;
mod repositorio;

use std::sync::{Arc, OnceLock};

use anyhow::Result;

use crate::config::{citizen_data::CitizenDataConfig, citizen_ui::CitizenUiConfig};

use self::{
    cache::CacheSnapshot, montador::MontadorSnapshot, repositorio::RepositorioDadosCidadao,
};

pub use self::modelos::{
    CoverageCard, FeedCard, HeroSection, HighlightCard, MetricCard, RankingGroups, RankingItem,
    Snapshot, SnapshotMeta, UiPayload,
};

static SERVICO: OnceLock<Arc<ServicoCidadaoDeOlho>> = OnceLock::new();

/// Retorna a instância singleton do serviço público do app.
///
/// O backend usa uma instância compartilhada para:
/// - reaproveitar o cache em memória;
/// - evitar recarregar configuração a cada request;
/// - manter um ponto único de orquestração do snapshot.
pub fn servico_compartilhado() -> &'static Arc<ServicoCidadaoDeOlho> {
    SERVICO.get_or_init(|| {
        Arc::new(
            ServicoCidadaoDeOlho::load().expect("falha ao inicializar o servico Cidadão de Olho"),
        )
    })
}

#[derive(Clone)]
/// Fachada principal da feature `Cidadão de Olho`.
///
/// Esta struct não conhece detalhes de parsing ou agregação. Ela apenas
/// coordena as dependências internas:
/// - `RepositorioDadosCidadao`: lê e normaliza os artefatos locais;
/// - `MontadorSnapshot`: transforma entradas normalizadas em DTOs públicos;
/// - `CacheSnapshot`: guarda o último snapshot válido por fingerprint dos arquivos.
pub struct ServicoCidadaoDeOlho {
    repositorio: RepositorioDadosCidadao,
    montador: MontadorSnapshot,
    cache: CacheSnapshot,
}

impl ServicoCidadaoDeOlho {
    /// Carrega o serviço a partir das configurações de dados e interface.
    pub fn load() -> Result<Self> {
        let data_config = CitizenDataConfig::load()?;
        let ui_config = CitizenUiConfig::load()?;
        Ok(Self::new(data_config, ui_config))
    }

    /// Constrói o serviço explicitamente, útil para testes e composição.
    pub fn new(data_config: CitizenDataConfig, ui_config: CitizenUiConfig) -> Self {
        let repositorio = RepositorioDadosCidadao::new(data_config.clone());
        let montador = MontadorSnapshot::new(data_config.limits, ui_config);

        Self {
            repositorio,
            montador,
            cache: CacheSnapshot::new(),
        }
    }

    /// Retorna o snapshot público atual.
    ///
    /// Quando `refresh` é `false`, o serviço tenta reutilizar o último snapshot
    /// em cache desde que os arquivos monitorados não tenham mudado.
    /// Quando `refresh` é `true`, o snapshot é recalculado ignorando o cache.
    pub fn snapshot(&self, refresh: bool) -> Result<Snapshot> {
        let key = self.repositorio.chave_cache()?;

        if !refresh {
            if let Some(snapshot) = self.cache.get(&key)? {
                return Ok(snapshot);
            }
        }

        let entradas = self.repositorio.carregar_entradas()?;
        let snapshot = self.montador.build(entradas);
        self.cache.store(key, snapshot.clone())?;
        Ok(snapshot)
    }
}
