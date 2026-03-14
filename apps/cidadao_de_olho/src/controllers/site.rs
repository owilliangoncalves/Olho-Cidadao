//! Entrega da interface web pública.
//!
//! O backend serve o `index.html` gerado pelo frontend e faz fallback para uma
//! página mínima quando o bundle ainda não foi compilado.

use axum::{
    debug_handler,
    response::{Html, IntoResponse, Response},
};
use loco_rs::prelude::*;
use std::{fs, path::Path};

const MANIFEST_DIR: &str = env!("CARGO_MANIFEST_DIR");
const FALLBACK_HTML: &str = r#"<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Cidadão de Olho</title>
    <style>
      body {
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background: linear-gradient(180deg, #090b11 0%, #151926 100%);
        color: #f5f1e9;
        font-family: "Avenir Next", "Segoe UI", sans-serif;
      }
      main {
        width: min(92vw, 760px);
        padding: 32px;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 28px;
        background: rgba(255,255,255,0.05);
        box-shadow: 0 30px 80px rgba(0,0,0,0.35);
      }
      h1 { margin: 0 0 16px; font-size: 2rem; }
      p { line-height: 1.7; color: rgba(245,241,233,0.84); }
      code {
        display: inline-block;
        padding: 0.2rem 0.45rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.08);
      }
    </style>
  </head>
  <body>
    <main>
      <h1>Cidadão de Olho</h1>
      <p>A interface publica ainda nao foi compilada.</p>
      <p>Execute <code>npm install</code> e depois <code>npm run build</code> em <code>apps/Cidadão_de_olho/ui</code> para gerar a camada visual que o Loco.rs entrega em <code>/</code>.</p>
    </main>
  </body>
</html>"#;

#[debug_handler]
/// Entrega o HTML inicial da aplicação.
async fn index() -> Result<Response> {
    let html = load_index_html();
    Ok(Html(html).into_response())
}

/// Registra a rota raiz da interface web.
pub fn routes() -> Routes {
    Routes::new().add("/", get(index))
}

/// Lê o `index.html` do frontend compilado ou devolve um fallback explicativo.
fn load_index_html() -> String {
    let path = Path::new(MANIFEST_DIR).join("assets/static/ui/index.html");
    fs::read_to_string(path).unwrap_or_else(|_| FALLBACK_HTML.to_string())
}
