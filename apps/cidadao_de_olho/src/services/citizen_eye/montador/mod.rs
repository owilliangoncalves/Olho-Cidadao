//! Montagem do snapshot público a partir de entradas normalizadas.
//!
//! Este módulo concentra a lógica de agregação, ordenação e montagem dos DTOs
//! expostos pela API. Ele não lê arquivos diretamente e não conhece cache.

mod acumulador_snapshot;
mod combined_stats;
mod coverage;
mod feed;
mod glossario;
mod helpers;
mod highlights;
mod metadata;
mod montador_snapshot;
mod ranking;
mod snapshot_rankings;

pub(crate) use self::montador_snapshot::MontadorSnapshot;
