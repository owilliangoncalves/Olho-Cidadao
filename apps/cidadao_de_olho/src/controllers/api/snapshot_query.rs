use serde::Deserialize;

use super::deserialize_refresh_flag::deserialize_refresh_flag;

#[derive(Debug, Default, Deserialize)]
/// Query string aceita pelo endpoint de snapshot.
pub(super) struct SnapshotQuery {
    #[serde(default, deserialize_with = "deserialize_refresh_flag")]
    pub(super) refresh: bool,
}
