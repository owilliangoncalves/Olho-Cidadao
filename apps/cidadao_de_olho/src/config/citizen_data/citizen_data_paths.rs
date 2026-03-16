use serde::Deserialize;

#[derive(Clone, Debug, Deserialize)]
/// Caminhos dos artefatos usados para montar o snapshot público.
pub struct CitizenDataPaths {
    pub project_root: String,
    pub camara_csv: String,
    pub senado_dir: String,
    pub suppliers_jsonl: String,
}
