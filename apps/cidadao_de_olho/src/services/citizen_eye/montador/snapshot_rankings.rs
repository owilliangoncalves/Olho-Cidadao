use crate::services::citizen_eye::modelos::{RankingGroups, RankingItem};

pub(super) struct SnapshotRankings {
    pub(super) suppliers: Vec<RankingItem>,
    pub(super) agents: Vec<RankingItem>,
    pub(super) expenses: Vec<RankingItem>,
    pub(super) ufs: Vec<RankingItem>,
}

impl SnapshotRankings {
    pub(super) fn into_groups(self) -> RankingGroups {
        RankingGroups {
            fornecedores: self.suppliers,
            agentes: self.agents,
            tipos_despesa: self.expenses,
            ufs: self.ufs,
        }
    }
}
