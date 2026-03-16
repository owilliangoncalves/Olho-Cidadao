use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct TextosFeed {
    pub rotulo_navegacao: String,
    pub sobrelinha_navegacao: String,
    pub descricao_navegacao: String,
    pub descricao_secao: String,
    pub rotulo_atualizando: String,
    pub aba_todas: String,
    pub aba_camara: String,
    pub aba_senado: String,
    pub titulo_painel_leitura: String,
    pub descricao_painel_leitura: String,
    pub sobrelinha_painel_filtro: String,
    pub titulo_todas_fontes: String,
    pub descricao_painel_filtro_sem_busca: String,
    pub descricao_painel_filtro_com_busca: String,
    pub descricao_ranking: String,
}
