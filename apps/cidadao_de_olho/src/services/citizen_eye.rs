//! Orquestracao do snapshot publico do `Olho Cidadão`.
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

use crate::config::{
    citizen_data::CitizenDataConfig, citizen_ui::CitizenUiConfig, glossario::GlossarioConfig,
    textos::TextosConfig,
};

use self::{
    cache::CacheSnapshot, montador::MontadorSnapshot, repositorio::RepositorioDadosCidadao,
};

pub use self::modelos::{
    CoverageCard, FeedCard, HeroSection, HighlightCard, MetricCard, RankingGroups, RankingItem,
    Snapshot, SnapshotMeta, TermoGlossario, UiPayload,
};

static SERVICO: OnceLock<Arc<ServicoCidadaoDeOlho>> = OnceLock::new();

/// Retorna a instância singleton do serviço público do app.
///
/// O backend usa uma instância compartilhada para:
/// - reaproveitar o cache em memória;
/// - evitar recarregar configuração a cada request;
/// - manter um ponto único de orquestração do snapshot.
pub fn servico_compartilhado() -> Result<Arc<ServicoCidadaoDeOlho>> {
    get_or_try_init_arc(&SERVICO, ServicoCidadaoDeOlho::load)
}

#[derive(Clone)]
/// Fachada principal da feature `Olho Cidadão`.
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
        let glossario_config = GlossarioConfig::load()?;
        let textos_config = TextosConfig::load()?;
        Ok(Self::new(
            data_config,
            ui_config,
            glossario_config,
            textos_config,
        ))
    }

    /// Constrói o serviço explicitamente, útil para testes e composição.
    pub fn new(
        data_config: CitizenDataConfig,
        ui_config: CitizenUiConfig,
        glossario_config: GlossarioConfig,
        textos_config: TextosConfig,
    ) -> Self {
        let repositorio = RepositorioDadosCidadao::new(data_config.clone());
        let montador =
            MontadorSnapshot::new(data_config.limits, ui_config, glossario_config, textos_config);

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

    /// Retorna a configuracao publica da interface sem depender do snapshot.
    pub fn interface_publica(&self) -> UiPayload {
        self.montador.ui_publica()
    }
}

fn get_or_try_init_arc<T, F>(cell: &OnceLock<Arc<T>>, loader: F) -> Result<Arc<T>>
where
    F: FnOnce() -> Result<T>,
{
    if let Some(value) = cell.get() {
        return Ok(value.clone());
    }

    let value = Arc::new(loader()?);
    match cell.set(value.clone()) {
        Ok(()) => Ok(value),
        Err(_) => Ok(cell.get().cloned().unwrap_or(value)),
    }
}

#[cfg(test)]
mod tests {
    use std::{
        sync::{
            atomic::{AtomicUsize, Ordering},
            Arc, OnceLock,
        },
    };

    use anyhow::anyhow;

    use super::get_or_try_init_arc;

    #[test]
    fn singleton_inicializa_uma_vez() {
        let cell = OnceLock::new();
        let calls = AtomicUsize::new(0);

        let first = get_or_try_init_arc(&cell, || {
            calls.fetch_add(1, Ordering::SeqCst);
            Ok::<_, anyhow::Error>("snapshot-service".to_string())
        })
        .expect("primeira inicializacao deveria funcionar");

        let second = get_or_try_init_arc(&cell, || {
            calls.fetch_add(1, Ordering::SeqCst);
            Ok::<_, anyhow::Error>("outra-instancia".to_string())
        })
        .expect("segunda leitura deveria reutilizar a instancia");

        assert_eq!(calls.load(Ordering::SeqCst), 1);
        assert_eq!(Arc::as_ptr(&first), Arc::as_ptr(&second));
        assert_eq!(first.as_str(), "snapshot-service");
    }

    #[test]
    fn singleton_propagates_loader_error_without_panicking() {
        let cell = OnceLock::<Arc<String>>::new();

        let error = get_or_try_init_arc(&cell, || Err(anyhow!("configuracao ausente")))
            .expect_err("falha de inicializacao deveria retornar erro");

        assert!(error.to_string().contains("configuracao ausente"));
        assert!(cell.get().is_none());
    }
}
