//! Endpoints JSON públicos do `Cidadão de Olho`.
//!
//! Esta camada mantém o controller fino: recebe a requisição HTTP, delega ao
//! serviço de domínio e serializa o contrato final como JSON.

use axum::{debug_handler, extract::Query, response::Response};
use loco_rs::prelude::*;
use serde::{de, Deserialize, Deserializer};

use crate::services::citizen_eye::servico_compartilhado;

#[derive(Debug, Default, Deserialize)]
/// Query string aceita pelo endpoint de snapshot.
struct SnapshotQuery {
    #[serde(default, deserialize_with = "deserialize_refresh_flag")]
    refresh: bool,
}

fn deserialize_refresh_flag<'de, D>(deserializer: D) -> std::result::Result<bool, D::Error>
where
    D: Deserializer<'de>,
{
    let value = Option::<String>::deserialize(deserializer)?;
    let Some(value) = value.as_deref().map(str::trim) else {
        return Ok(false);
    };

    if value.is_empty() {
        return Ok(false);
    }

    match value.to_ascii_lowercase().as_str() {
        "1" | "true" | "t" | "yes" | "y" => Ok(true),
        "0" | "false" | "f" | "no" | "n" => Ok(false),
        _ => Err(de::Error::custom(
            "refresh deve ser um booleano valido: use 1/0 ou true/false",
        )),
    }
}

#[debug_handler]
/// Healthcheck simples para monitoração da aplicação.
async fn health() -> Result<Response> {
    format::json(serde_json::json!({
        "status": "ok",
        "service": "cidadao_de_olho",
    }))
}

#[debug_handler]
/// Entrega o snapshot público consolidado consumido pelo frontend.
///
/// O cálculo roda em `spawn_blocking` porque envolve leitura de disco e
/// agregação síncrona de artefatos locais.
async fn snapshot(Query(query): Query<SnapshotQuery>) -> Result<Response> {
    let refresh = query.refresh;
    let service = servico_compartilhado().map_err(|error| Error::string(&error.to_string()))?;
    let snapshot = tokio::task::spawn_blocking(move || service.snapshot(refresh))
        .await
        .map_err(|error| Error::string(&format!("falha ao aguardar snapshot: {error}")))?
        .map_err(|error| Error::string(&error.to_string()))?;

    format::json(snapshot)
}

/// Registra as rotas públicas da API.
pub fn routes() -> Routes {
    Routes::new()
        .prefix("/api")
        .add("/health", get(health))
        .add("/snapshot", get(snapshot))
}

#[cfg(test)]
mod tests {
    use super::SnapshotQuery;

    #[test]
    fn aceita_refresh_numerico() {
        let query = serde_urlencoded::from_str::<SnapshotQuery>("refresh=1")
            .expect("query string deveria ser aceita");

        assert!(query.refresh);
    }

    #[test]
    fn aceita_refresh_booleano() {
        let query = serde_urlencoded::from_str::<SnapshotQuery>("refresh=true")
            .expect("query string deveria ser aceita");

        assert!(query.refresh);
    }

    #[test]
    fn rejeita_refresh_invalido() {
        let error = serde_urlencoded::from_str::<SnapshotQuery>("refresh=agora")
            .expect_err("query string invalida deveria falhar");

        assert!(error.to_string().contains("refresh deve ser um booleano valido"));
    }
}
