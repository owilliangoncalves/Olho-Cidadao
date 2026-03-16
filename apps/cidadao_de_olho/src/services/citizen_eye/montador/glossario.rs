use crate::services::citizen_eye::modelos::TermoGlossario;

use super::montador_snapshot::MontadorSnapshot;

impl MontadorSnapshot {
    /// Constrói a lista do glossário.
    pub(super) fn build_glossario(&self) -> Vec<TermoGlossario> {
        self.glossario_config
            .termos
            .iter()
            .map(TermoGlossario::from_config)
            .collect()
    }
}
