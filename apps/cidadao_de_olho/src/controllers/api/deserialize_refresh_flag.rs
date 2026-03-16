use serde::{de, Deserialize, Deserializer};

pub(super) fn deserialize_refresh_flag<'de, D>(
    deserializer: D,
) -> std::result::Result<bool, D::Error>
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
