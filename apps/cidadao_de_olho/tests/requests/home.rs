//! Smoke tests HTTP do `Olho Cidadão`.
//!
//! Estes testes garantem que a app sobe, entrega o HTML inicial e expõe o
//! snapshot público com o contrato esperado.

use cidadao_de_olho::app::App;
use loco_rs::testing::prelude::*;
use serial_test::serial;

#[tokio::test]
#[serial]
/// Garante que a rota raiz entrega a interface pública.
async fn can_get_home() {
    unsafe {
        std::env::set_var("LOCO_ENV", "test");
    }

    request::<App, _, _>(|request, _ctx| async move {
        let res = request.get("/").await;

        assert_eq!(res.status_code(), 200);
        let body = res.text();
        assert!(body.contains("Olho Cidadão"));
    })
    .await;
}

#[tokio::test]
#[serial]
/// Garante que a configuracao textual publica pode ser lida separadamente.
async fn can_get_public_interface_texts() {
    unsafe {
        std::env::set_var("LOCO_ENV", "test");
    }

    request::<App, _, _>(|request, _ctx| async move {
        let res = request.get("/api/interface").await;

        assert_eq!(res.status_code(), 200);
        let body = res.json::<serde_json::Value>();
        assert_eq!(body["textos"]["visao_geral"]["rotulo_navegacao"], "Inicio");
    })
    .await;
}

#[tokio::test]
#[serial]
/// Garante que o endpoint de snapshot responde com o contrato básico esperado.
async fn can_get_snapshot() {
    unsafe {
        std::env::set_var("LOCO_ENV", "test");
    }

    request::<App, _, _>(|request, _ctx| async move {
        let res = request.get("/api/snapshot").await;

        assert_eq!(res.status_code(), 200);
        let body = res.json::<serde_json::Value>();
        assert_eq!(body["meta"]["title"], "Olho Cidadão");
        assert_eq!(body["meta"]["sources"], serde_json::json!(["camara", "senado"]));
        assert!(body["feed"].as_array().is_some());
        assert!(body["glossario"].as_array().is_some());
        assert_eq!(body["coverage"][0]["source"], "Câmara");
    })
    .await;
}

#[tokio::test]
#[serial]
/// Garante que o contrato documentado de refresh numerico continua aceito.
async fn can_get_snapshot_with_numeric_refresh_flag() {
    unsafe {
        std::env::set_var("LOCO_ENV", "test");
    }

    request::<App, _, _>(|request, _ctx| async move {
        let res = request.get("/api/snapshot?refresh=1").await;

        assert_eq!(res.status_code(), 200);
        let body = res.json::<serde_json::Value>();
        assert!(body["feed"].as_array().is_some());
    })
    .await;
}

#[tokio::test]
#[serial]
/// Garante que valores invalidos de refresh falham com erro de uso.
async fn rejects_invalid_refresh_flag() {
    unsafe {
        std::env::set_var("LOCO_ENV", "test");
    }

    request::<App, _, _>(|request, _ctx| async move {
        let res = request.get("/api/snapshot?refresh=agora").await;

        assert_eq!(res.status_code(), 400);
    })
    .await;
}
