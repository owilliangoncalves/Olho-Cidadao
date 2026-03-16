use std::path::Path;

use cidadao_de_olho::config::{
    citizen_data::CitizenDataConfig, citizen_ui::CitizenUiConfig, glossario::GlossarioConfig,
    textos::TextosConfig,
};

#[test]
fn carrega_configuracao_de_dados() {
    let config = CitizenDataConfig::load().expect("configuracao de dados deve carregar");

    assert!(config.limits.max_feed_items > 0);
    assert!(config.limits.max_ranking_items > 0);
    assert!(!config.paths.project_root.is_empty());
}

#[test]
fn resolve_caminhos_derivados_a_partir_da_configuracao() {
    let config = CitizenDataConfig::load().expect("configuracao de dados deve carregar");

    assert!(config.camara_csv_path().is_absolute());
    assert!(config.senado_dir_path().is_absolute());
    assert!(config.suppliers_jsonl_path().is_absolute());
    assert!(config
        .project_root()
        .starts_with(Path::new(env!("CARGO_MANIFEST_DIR"))));
}

#[test]
fn carrega_configuracao_de_interface() {
    let config = CitizenUiConfig::load().expect("configuracao de interface deve carregar");

    assert!(!config.branding.title.is_empty());
    assert!(!config.branding.headline.is_empty());
    assert!(!config.copy.feed_title.is_empty());
    assert!(!config.copy.methodology.is_empty());
}

#[test]
fn carrega_glossario_editorial() {
    let config = GlossarioConfig::load().expect("glossario deve carregar");

    assert!(!config.termos.is_empty());
    assert!(!config.termos[0].termo.is_empty());
    assert!(!config.termos[0].definicao.is_empty());
}

#[test]
fn carrega_textos_com_secao_para_cada_pagina() {
    let config = TextosConfig::load().expect("configuracao textual deve carregar");

    assert_eq!(config.visao_geral.rotulo_navegacao, "Início");
    assert_eq!(config.feed.rotulo_navegacao, "Feed");
    assert_eq!(config.rankings.rotulo_navegacao, "Rankings");
    assert_eq!(config.cobertura.rotulo_navegacao, "Cobertura");
    assert_eq!(config.glossario.rotulo_navegacao, "Glossario");

    assert!(!config.barra_superior.atualizado_prefixo.is_empty());
    assert!(!config.compartilhado.botao_metodologia.is_empty());
    assert!(!config.estados.carregando_titulo.is_empty());
}
