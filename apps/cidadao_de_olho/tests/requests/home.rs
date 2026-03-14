//! Smoke tests HTTP do `Cidadão de Olho`.
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
        assert!(body.contains("Cidadao de Olho"));
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
        assert_eq!(body["meta"]["title"], "Cidadao de Olho");
        assert!(body["feed"].as_array().is_some());
        assert_eq!(body["coverage"][0]["source"], "Câmara");
    })
    .await;
}
