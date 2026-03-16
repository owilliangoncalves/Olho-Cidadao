//! Configuracao central de textos renderizados na interface publica.
//!
//! Cada secao do TOML representa uma pagina ou uma area compartilhada da
//! experiencia, evitando copy hardcoded na camada React.

use std::path::Path;

use anyhow::Result;
use serde::{Deserialize, Serialize};

use super::carregador::carregar_config_toml;

const MANIFEST_DIR: &str = env!("CARGO_MANIFEST_DIR");

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct TextosConfig {
    pub barra_superior: TextosBarraSuperior,
    pub estados: TextosEstados,
    pub compartilhado: TextosCompartilhados,
    pub visao_geral: TextosVisaoGeral,
    pub feed: TextosFeed,
    pub rankings: TextosRankings,
    pub cobertura: TextosCobertura,
    pub glossario: TextosGlossario,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct TextosBarraSuperior {
    pub subtitulo: String,
    pub atualizado_prefixo: String,
    pub cobertura_prefixo: String,
    pub cobertura_em_carga: String,
    pub rotulo_aria_navegacao: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct TextosEstados {
    pub carregando_sobrelinha: String,
    pub carregando_titulo: String,
    pub carregando_descricao: String,
    pub falha_sobrelinha: String,
    pub falha_titulo: String,
    pub botao_tentar_novamente: String,
}

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

impl TextosConfig {
    /// Carrega os textos centralizados da interface.
    pub fn load() -> Result<Self> {
        let path = Path::new(MANIFEST_DIR).join("config").join("textos.toml");
        carregar_config_toml(&path)
    }
}

#[cfg(test)]
mod tests {
    use super::TextosConfig;

    #[test]
    fn carrega_textos_com_secao_para_cada_pagina() {
        let config = TextosConfig::load().expect("configuracao textual deve carregar");

        assert_eq!(config.visao_geral.rotulo_navegacao, "Inicio");
        assert_eq!(config.feed.rotulo_navegacao, "Feed");
        assert_eq!(config.rankings.rotulo_navegacao, "Rankings");
        assert_eq!(config.cobertura.rotulo_navegacao, "Cobertura");
        assert_eq!(config.glossario.rotulo_navegacao, "Glossario");

        assert!(!config.barra_superior.subtitulo.is_empty());
        assert!(!config.compartilhado.botao_metodologia.is_empty());
        assert!(!config.estados.carregando_titulo.is_empty());
    }
}
