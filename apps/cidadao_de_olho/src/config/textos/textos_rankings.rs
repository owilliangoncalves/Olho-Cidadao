use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct TextosRankings {
    pub rotulo_navegacao: String,
    pub sobrelinha_navegacao: String,
    pub descricao_navegacao: String,
    pub sobrelinha_secao: String,
    pub titulo_secao: String,
    pub descricao_secao: String,
    pub aba_fornecedores: String,
    pub aba_agentes: String,
    pub aba_tipos: String,
    pub aba_ufs: String,
    pub sobrelinha_painel_fornecedores: String,
    pub descricao_painel_fornecedores: String,
    pub sobrelinha_painel_agentes: String,
    pub descricao_painel_agentes: String,
    pub sobrelinha_painel_tipos: String,
    pub descricao_painel_tipos: String,
    pub titulo_painel_ufs: String,
    pub sobrelinha_painel_ufs: String,
    pub descricao_painel_ufs: String,
    pub sobrelinha_ajuda: String,
    pub titulo_ajuda: String,
    pub descricao_ajuda: String,
}
