//! Funções puras de parsing e formatação.
//!
//! Estas utilidades ficam isoladas para que regras de normalização textual,
//! datas e moeda possam ser reutilizadas sem acoplar repositório e montador.

use chrono::{Datelike, NaiveDate};

/// Retorna o texto tratado ou um fallback quando o valor está ausente.
pub(crate) fn fallback_text(value: Option<&str>, fallback: &str) -> String {
    value
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(str::to_string)
        .unwrap_or_else(|| fallback.to_string())
}

/// Normaliza um campo opcional removendo espaços e descartando strings vazias.
pub(crate) fn normalize_optional(value: Option<&str>) -> Option<String> {
    value
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(str::to_string)
}

/// Converte representações monetárias heterogêneas em `f64`.
pub(crate) fn parse_float(value: Option<&str>) -> f64 {
    let Some(raw) = value.map(str::trim).filter(|value| !value.is_empty()) else {
        return 0.0;
    };

    let normalized = if raw.contains(',') {
        raw.replace('.', "").replace(',', ".")
    } else {
        raw.to_string()
    };

    normalized.replace("R$", "").parse::<f64>().unwrap_or(0.0)
}

/// Converte um inteiro textual opcional em `i32`.
pub(crate) fn parse_int(value: Option<&str>) -> i32 {
    value
        .map(str::trim)
        .and_then(|value| value.parse::<i32>().ok())
        .unwrap_or_default()
}

/// Converte um mês textual em `u32`, aceitando apenas `1..=12`.
pub(crate) fn parse_month(value: Option<&str>) -> u32 {
    value
        .map(str::trim)
        .and_then(|value| value.parse::<u32>().ok())
        .filter(|value| (1..=12).contains(value))
        .unwrap_or(1)
}

/// Converte uma data ISO (`YYYY-MM-DD`) em chave numérica de ordenação.
pub(crate) fn parse_date_key(value: &str) -> Option<i64> {
    NaiveDate::parse_from_str(value, "%Y-%m-%d")
        .ok()
        .map(|date| {
            i64::from(date.year()) * 10_000 + i64::from(date.month()) * 100 + i64::from(date.day())
        })
}

/// Gera um rótulo curto de período para exibição pública.
pub(crate) fn period_label(year: i32, month: u32) -> String {
    const MONTHS: [&str; 12] = [
        "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez",
    ];
    let label = MONTHS
        .get(month.saturating_sub(1) as usize)
        .copied()
        .unwrap_or("mes");
    format!("{label}/{year}")
}

/// Formata valores monetários no padrão visual brasileiro.
pub(crate) fn format_currency(value: f64) -> String {
    let rounded = format!("{value:.2}");
    let (integer, fraction) = rounded.split_once('.').unwrap_or((&rounded, "00"));
    let integer = integer
        .chars()
        .rev()
        .enumerate()
        .fold(String::new(), |mut output, (index, ch)| {
            if index > 0 && index % 3 == 0 {
                output.push('.');
            }
            output.push(ch);
            output
        })
        .chars()
        .rev()
        .collect::<String>();
    format!("R$ {integer},{fraction}")
}

/// Calcula a participação relativa de um valor no total.
pub(crate) fn share_of(total: f64, value: f64) -> f64 {
    if total <= 0.0 {
        return 0.0;
    }
    value / total
}

/// Formata participação relativa como percentual curto.
pub(crate) fn format_share(value: f64) -> String {
    format!("{:.1}%", value * 100.0)
}

#[cfg(test)]
mod testes {
    use super::{format_currency, parse_date_key, period_label};

    #[test]
    fn formats_brazilian_currency() {
        assert_eq!(format_currency(681_225_965.34), "R$ 681.225.965,34");
    }

    #[test]
    fn builds_period_label() {
        assert_eq!(period_label(2025, 3), "mar/2025");
    }

    #[test]
    fn parses_date_sort_key() {
        assert_eq!(parse_date_key("2025-03-14"), Some(20250314));
    }
}
