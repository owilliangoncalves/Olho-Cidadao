use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct TextosBarraSuperior {
    pub subtitulo: String,
    pub atualizado_prefixo: String,
    pub cobertura_prefixo: String,
    pub cobertura_em_carga: String,
    pub rotulo_aria_navegacao: String,
}
