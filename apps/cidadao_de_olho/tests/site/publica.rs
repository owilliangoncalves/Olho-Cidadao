use cidadao_de_olho::app::App;
use loco_rs::testing::prelude::*;
use serial_test::serial;

#[tokio::test]
#[serial]
async fn raiz_entrega_html_publico() {
    unsafe {
        std::env::set_var("LOCO_ENV", "test");
    }

    request::<App, _, _>(|request, _ctx| async move {
        let res = request.get("/").await;

        assert_eq!(res.status_code(), 200);
        let body = res.text();
        assert!(body.contains("<html"));
        assert!(body.contains("Cidadão de Olho"));
    })
    .await;
}

#[tokio::test]
#[serial]
async fn raiz_entrega_documento_com_titulo() {
    unsafe {
        std::env::set_var("LOCO_ENV", "test");
    }

    request::<App, _, _>(|request, _ctx| async move {
        let res = request.get("/").await;

        assert_eq!(res.status_code(), 200);
        let body = res.text();
        assert!(body.contains("<title>"));
    })
    .await;
}
