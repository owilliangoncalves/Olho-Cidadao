use serde::Serialize;

#[derive(Clone, Debug, Serialize)]
/// Bloco principal de abertura da interface.
pub struct HeroSection {
    pub eyebrow: String,
    pub headline: String,
    pub subheadline: String,
    pub metrics: Vec<MetricCard>,
}

#[derive(Clone, Debug, Serialize)]
/// Métrica resumida exibida no hero da aplicação.
pub struct MetricCard {
    pub label: String,
    pub value: String,
    pub detail: String,
    pub tone: String,
}

#[derive(Clone, Debug, Serialize)]
/// Card de destaque rápido exibido no topo da experiência.
pub struct HighlightCard {
    pub title: String,
    pub value: String,
    pub detail: String,
}
