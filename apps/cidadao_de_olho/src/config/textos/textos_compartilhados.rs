use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct TextosCompartilhados {
    pub sobrelinha_guia_rapido: String,
    pub sobrelinha_leitura_curta: String,
    pub botao_metodologia: String,
    pub dica_metodologia: String,
    pub tooltip_tag: String,
    pub sobrelinha_ao_vivo: String,
    pub sobrelinha_quem_aparece_agora: String,
    pub cartao_cobertura_registros: String,
    pub cartao_cobertura_agentes: String,
    pub cartao_cobertura_fornecedores: String,
    pub cartao_feed_agente: String,
    pub cartao_feed_fornecedor: String,
    pub cartao_feed_valor: String,
    pub cartao_feed_documento_ausente: String,
}
