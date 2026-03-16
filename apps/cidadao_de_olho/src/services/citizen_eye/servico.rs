use anyhow::Result;

use crate::config::{
    citizen_data::CitizenDataConfig, citizen_ui::CitizenUiConfig, glossario::GlossarioConfig,
    textos::TextosConfig,
};

use super::{
    cache::CacheSnapshot, montador::MontadorSnapshot, repositorio::RepositorioDadosCidadao,
    Snapshot, UiPayload,
};

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
    #[must_use]
    pub fn new(
        data_config: CitizenDataConfig,
        ui_config: CitizenUiConfig,
        glossario_config: GlossarioConfig,
        textos_config: TextosConfig,
    ) -> Self {
        let repositorio = RepositorioDadosCidadao::new(data_config.clone());
        let montador = MontadorSnapshot::new(
            data_config.limits,
            ui_config,
            glossario_config,
            textos_config,
        );

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
    #[must_use]
    pub fn interface_publica(&self) -> UiPayload {
        self.montador.ui_publica()
    }
}
