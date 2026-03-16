use cidadao_de_olho::app::App;
use loco_rs::testing::prelude::*;
use serial_test::serial;

#[tokio::test]
#[serial]
async fn health_retorna_status_ok() {
    unsafe {
        std::env::set_var("LOCO_ENV", "test");
    }

    request::<App, _, _>(|request, _ctx| async move {
        let res = request.get("/api/health").await;

        assert_eq!(res.status_code(), 200);
        let body = res.json::<serde_json::Value>();
        assert_eq!(body["status"], "ok");
        assert_eq!(body["service"], "cidadao_de_olho");
    })
    .await;
}

#[tokio::test]
#[serial]
async fn snapshot_aceita_refresh_numerico() {
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
async fn snapshot_aceita_refresh_booleano() {
    unsafe {
        std::env::set_var("LOCO_ENV", "test");
    }

    request::<App, _, _>(|request, _ctx| async move {
        let res = request.get("/api/snapshot?refresh=true").await;

        assert_eq!(res.status_code(), 200);
        let body = res.json::<serde_json::Value>();
        assert!(body["feed"].as_array().is_some());
    })
    .await;
}

#[tokio::test]
#[serial]
async fn snapshot_rejeita_refresh_invalido() {
    unsafe {
        std::env::set_var("LOCO_ENV", "test");
    }

    request::<App, _, _>(|request, _ctx| async move {
        let res = request.get("/api/snapshot?refresh=agora").await;

        assert_eq!(res.status_code(), 400);
    })
    .await;
}
