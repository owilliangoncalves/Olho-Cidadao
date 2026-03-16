use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct TextosEstados {
    pub carregando_sobrelinha: String,
    pub carregando_titulo: String,
    pub carregando_descricao: String,
    pub falha_sobrelinha: String,
    pub falha_titulo: String,
    pub botao_tentar_novamente: String,
}
