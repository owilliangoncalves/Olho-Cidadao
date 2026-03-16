//! Endpoints JSON públicos do `Olho Cidadão`.
//!
//! Esta camada mantém o controller fino: recebe a requisição HTTP, delega ao
//! serviço de domínio e serializa o contrato final como JSON.

mod deserialize_refresh_flag;
mod health;
mod interface;
mod routes;
mod snapshot;
mod snapshot_query;

pub use self::routes::routes;
