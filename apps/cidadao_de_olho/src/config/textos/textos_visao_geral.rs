use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct TextosVisaoGeral {
    pub rotulo_navegacao: String,
    pub sobrelinha_navegacao: String,
    pub descricao_navegacao: String,
    pub botao_abrir_feed: String,
    pub botao_ver_cobertura: String,
    pub sobrelinha_radar: String,
    pub titulo_radar: String,
    pub descricao_radar: String,
    pub titulo_leitura: String,
    pub descricao_leitura: String,
    pub titulo_cobertura: String,
    pub descricao_cobertura: String,
}
