//! Cache em memória do snapshot público.
//!
//! O cache é propositalmente simples: guarda apenas o último snapshot e a
//! assinatura dos arquivos usados para gerá-lo. Se qualquer arquivo mudar,
//! o cache deixa de valer.

use std::sync::{Arc, RwLock};

use anyhow::{anyhow, Result};

use super::modelos::Snapshot;

#[derive(Clone, Debug, Eq, PartialEq)]
/// Assinatura mínima de um arquivo relevante para o snapshot.
pub(crate) struct AssinaturaArquivo {
    pub path: String,
    pub modified_ns: u128,
    pub size: u64,
}

pub(crate) type ChaveCache = Vec<AssinaturaArquivo>;

#[derive(Clone)]
struct SnapshotEmCache {
    key: ChaveCache,
    snapshot: Snapshot,
}

#[derive(Clone, Default)]
/// Cache thread-safe para o último snapshot produzido.
pub(crate) struct CacheSnapshot {
    inner: Arc<RwLock<Option<SnapshotEmCache>>>,
}

impl CacheSnapshot {
    /// Cria um cache vazio.
    pub(crate) fn new() -> Self {
        Self::default()
    }

    /// Retorna o snapshot armazenado quando a chave bate exatamente.
    pub(crate) fn get(&self, key: &ChaveCache) -> Result<Option<Snapshot>> {
        let guard = self
            .inner
            .read()
            .map_err(|_| anyhow!("falha ao acessar cache de leitura"))?;

        Ok(guard
            .as_ref()
            .filter(|cached| &cached.key == key)
            .map(|cached| cached.snapshot.clone()))
    }

    /// Substitui o conteúdo do cache pela versão mais recente do snapshot.
    pub(crate) fn store(&self, key: ChaveCache, snapshot: Snapshot) -> Result<()> {
        let mut guard = self
            .inner
            .write()
            .map_err(|_| anyhow!("falha ao acessar cache de escrita"))?;

        *guard = Some(SnapshotEmCache { key, snapshot });
        Ok(())
    }
}
