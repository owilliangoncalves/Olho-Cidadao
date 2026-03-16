use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct TextosGlossario {
    pub rotulo_navegacao: String,
    pub sobrelinha_navegacao: String,
    pub descricao_navegacao: String,
    pub sobrelinha_secao: String,
    pub titulo_secao: String,
    pub descricao_secao: String,
    pub rotulo_busca: String,
    pub placeholder_busca: String,
    pub rotulo_contador_termos: String,
    pub mensagem_vazia: String,
    pub rotulo_contexto: String,
    pub sobrelinha_leitura: String,
    pub titulo_leitura: String,
    pub descricao_leitura: String,
    pub titulo_como_usar: String,
    pub passo_1_como_usar: String,
    pub passo_2_como_usar: String,
    pub passo_3_como_usar: String,
    pub titulo_dica: String,
    pub descricao_dica: String,
    pub descricao_grupo_leitura_do_dado: String,
    pub descricao_grupo_interface: String,
    pub descricao_grupo_metodo: String,
}
