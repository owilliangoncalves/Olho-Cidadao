use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct TextosCobertura {
    pub rotulo_navegacao: String,
    pub sobrelinha_navegacao: String,
    pub descricao_navegacao: String,
    pub sobrelinha_secao: String,
    pub titulo_secao: String,
    pub descricao_secao: String,
    pub aba_fontes: String,
    pub aba_destaques: String,
    pub aba_notas: String,
    pub sobrelinha_contrato: String,
    pub titulo_contrato: String,
    pub descricao_contrato: String,
}
