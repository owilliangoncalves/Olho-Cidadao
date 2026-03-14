//! Leitura e normalização dos artefatos produzidos pelo ETL.
//!
//! O repositório transforma CSV, JSON e JSONL heterogêneos em estruturas
//! internas uniformes. Isso reduz o acoplamento entre formato de arquivo e
//! lógica de apresentação.

use std::{
    fs::{self, File},
    io::{BufRead, BufReader},
    path::PathBuf,
};

use anyhow::{Context, Result};
use csv::ReaderBuilder;
use serde::Deserialize;

use crate::config::citizen_data::CitizenDataConfig;

use super::{
    cache::{AssinaturaArquivo, ChaveCache},
    dominio::{EntradasSnapshot, FontePublica, RegistroDespesa},
    formatacao::{
        fallback_text, normalize_optional, parse_date_key, parse_float, parse_int, parse_month,
        period_label,
    },
};

#[derive(Clone)]
/// Repositório de leitura dos artefatos locais usados pelo app.
pub(crate) struct RepositorioDadosCidadao {
    config: CitizenDataConfig,
}

#[derive(Clone, Debug, Deserialize)]
struct SupplierRecord {
    documento: String,
    nome_principal: String,
}

#[derive(Clone, Debug, Deserialize)]
struct CamaraRow {
    id_deputado: Option<String>,
    nome_deputado: Option<String>,
    sigla_uf_deputado: Option<String>,
    sigla_partido_deputado: Option<String>,
    #[serde(rename = "nomeFornecedor")]
    nome_fornecedor: Option<String>,
    documento_fornecedor_normalizado: Option<String>,
    #[serde(rename = "valorLiquido")]
    valor_liquido: Option<String>,
    ano: Option<String>,
    mes: Option<String>,
    #[serde(rename = "tipoDespesa")]
    tipo_despesa: Option<String>,
}

#[derive(Clone, Debug, Deserialize)]
struct SenadoRow {
    ano: Option<i32>,
    mes: Option<u32>,
    data: Option<String>,
    #[serde(rename = "codSenador")]
    cod_senador: Option<i32>,
    #[serde(rename = "nomeSenador")]
    nome_senador: Option<String>,
    #[serde(rename = "tipoDespesa")]
    tipo_despesa: Option<String>,
    fornecedor: Option<String>,
    #[serde(rename = "valorReembolsado")]
    valor_reembolsado: Option<f64>,
    documento_fornecedor_normalizado: Option<String>,
}

impl RepositorioDadosCidadao {
    /// Cria o repositório com a configuração de caminhos e limites.
    pub(crate) fn new(config: CitizenDataConfig) -> Self {
        Self { config }
    }

    /// Calcula a assinatura dos arquivos que influenciam o snapshot.
    pub(crate) fn chave_cache(&self) -> Result<ChaveCache> {
        let mut files = vec![
            self.config.camara_csv_path(),
            self.config.suppliers_jsonl_path(),
        ];
        files.extend(self.senado_paths()?);

        let mut key = Vec::with_capacity(files.len());
        for path in files {
            if let Ok(metadata) = fs::metadata(&path) {
                let modified_ns = metadata
                    .modified()
                    .ok()
                    .and_then(|value| value.duration_since(std::time::UNIX_EPOCH).ok())
                    .map_or(0, |value| value.as_nanos());
                key.push(AssinaturaArquivo {
                    path: path.display().to_string(),
                    modified_ns,
                    size: metadata.len(),
                });
            } else {
                key.push(AssinaturaArquivo {
                    path: path.display().to_string(),
                    modified_ns: 0,
                    size: 0,
                });
            }
        }

        Ok(key)
    }

    /// Lê todos os artefatos e devolve entradas normalizadas para o montador.
    pub(crate) fn carregar_entradas(&self) -> Result<EntradasSnapshot> {
        let (supplier_aliases, supplier_dimension_count) = self.load_supplier_dimension()?;
        let mut records = Vec::new();

        self.carregar_camara(&supplier_aliases, &mut records)?;
        self.carregar_senado(&supplier_aliases, &mut records)?;

        Ok(EntradasSnapshot {
            supplier_dimension_count,
            records,
        })
    }

    /// Carrega a dimensão de fornecedores usada para enriquecer nomes por documento.
    fn load_supplier_dimension(
        &self,
    ) -> Result<(std::collections::HashMap<String, String>, usize)> {
        let path = self.config.suppliers_jsonl_path();
        if !path.exists() {
            return Ok((std::collections::HashMap::new(), 0));
        }

        let file = File::open(&path)
            .with_context(|| format!("nao foi possivel abrir {}", path.display()))?;
        let reader = BufReader::new(file);
        let mut aliases = std::collections::HashMap::new();
        let mut count = 0usize;

        for line in reader.lines() {
            let line = line?;
            if line.trim().is_empty() {
                continue;
            }
            let record: SupplierRecord = serde_json::from_str(&line)
                .with_context(|| format!("linha JSONL invalida em {}", path.display()))?;
            aliases.insert(record.documento, record.nome_principal);
            count += 1;
        }

        Ok((aliases, count))
    }

    /// Lê o CSV consolidado da Câmara e o transforma em registros normalizados.
    fn carregar_camara(
        &self,
        supplier_aliases: &std::collections::HashMap<String, String>,
        records: &mut Vec<RegistroDespesa>,
    ) -> Result<()> {
        let path = self.config.camara_csv_path();
        if !path.exists() {
            return Ok(());
        }

        let mut reader = ReaderBuilder::new()
            .flexible(true)
            .from_path(&path)
            .with_context(|| format!("nao foi possivel abrir {}", path.display()))?;

        for row in reader.deserialize::<CamaraRow>() {
            let row = row.with_context(|| format!("linha CSV invalida em {}", path.display()))?;

            let value = parse_float(row.valor_liquido.as_deref());
            let year = parse_int(row.ano.as_deref());
            let month = parse_month(row.mes.as_deref());
            let actor = fallback_text(row.nome_deputado.as_deref(), "Deputado nao identificado");
            let party = fallback_text(row.sigla_partido_deputado.as_deref(), "Sem partido");
            let uf = fallback_text(row.sigla_uf_deputado.as_deref(), "BR");
            let supplier_doc = normalize_optional(row.documento_fornecedor_normalizado.as_deref());
            let supplier = supplier_doc
                .as_ref()
                .and_then(|doc| supplier_aliases.get(doc))
                .cloned()
                .unwrap_or_else(|| {
                    fallback_text(
                        row.nome_fornecedor.as_deref(),
                        "Fornecedor nao identificado",
                    )
                });
            let expense_type =
                fallback_text(row.tipo_despesa.as_deref(), "Despesa nao classificada");
            let actor_rank_key = format!(
                "camara:{}",
                row.id_deputado
                    .as_deref()
                    .map(str::trim)
                    .filter(|value| !value.is_empty())
                    .unwrap_or(actor.as_str())
            );

            records.push(RegistroDespesa {
                source: FontePublica::Camara,
                sort_key: i64::from(year) * 100 + i64::from(month),
                amount_value: value,
                year,
                period: period_label(year, month),
                actor,
                actor_meta: format!("{party} • {uf}"),
                actor_rank_key,
                supplier,
                supplier_doc,
                expense_type,
                tags: vec!["Camara".to_string(), uf.clone(), party, year.to_string()],
                uf: Some(uf),
            });
        }

        Ok(())
    }

    /// Lê os JSONs do Senado e os transforma em registros normalizados.
    fn carregar_senado(
        &self,
        supplier_aliases: &std::collections::HashMap<String, String>,
        records: &mut Vec<RegistroDespesa>,
    ) -> Result<()> {
        for path in self.senado_paths()? {
            let file = File::open(&path)
                .with_context(|| format!("nao foi possivel abrir {}", path.display()))?;
            let reader = BufReader::new(file);

            for line in reader.lines() {
                let line = line?;
                if line.trim().is_empty() {
                    continue;
                }
                let row: SenadoRow = serde_json::from_str(&line)
                    .with_context(|| format!("linha JSON invalida em {}", path.display()))?;

                let value = row.valor_reembolsado.unwrap_or(0.0);
                let year = row.ano.unwrap_or_default();
                let month = row.mes.unwrap_or(1);
                let actor = fallback_text(row.nome_senador.as_deref(), "Senador nao identificado");
                let supplier_doc =
                    normalize_optional(row.documento_fornecedor_normalizado.as_deref());
                let supplier = supplier_doc
                    .as_ref()
                    .and_then(|doc| supplier_aliases.get(doc))
                    .cloned()
                    .unwrap_or_else(|| {
                        fallback_text(row.fornecedor.as_deref(), "Fornecedor nao identificado")
                    });
                let expense_type =
                    fallback_text(row.tipo_despesa.as_deref(), "Despesa nao classificada");
                let period = row
                    .data
                    .as_deref()
                    .map(str::to_string)
                    .unwrap_or_else(|| period_label(year, month));
                let sort_key = row
                    .data
                    .as_deref()
                    .and_then(parse_date_key)
                    .unwrap_or_else(|| i64::from(year) * 100 + i64::from(month));

                records.push(RegistroDespesa {
                    source: FontePublica::Senado,
                    sort_key,
                    amount_value: value,
                    year,
                    period,
                    actor: actor.clone(),
                    actor_meta: "Senado Federal".to_string(),
                    actor_rank_key: format!(
                        "senado:{}",
                        row.cod_senador
                            .map(|value| value.to_string())
                            .unwrap_or(actor)
                    ),
                    supplier,
                    supplier_doc,
                    expense_type,
                    tags: vec!["Senado".to_string(), year.to_string()],
                    uf: None,
                });
            }
        }

        Ok(())
    }

    fn senado_paths(&self) -> Result<Vec<PathBuf>> {
        let dir = self.config.senado_dir_path();
        if !dir.exists() {
            return Ok(vec![]);
        }

        let mut paths = fs::read_dir(&dir)
            .with_context(|| format!("nao foi possivel listar {}", dir.display()))?
            .filter_map(|entry| entry.ok().map(|value| value.path()))
            .filter(|path| {
                path.extension().and_then(|ext| ext.to_str()) == Some("json") && path.is_file()
            })
            .collect::<Vec<_>>();
        paths.sort();
        Ok(paths)
    }
}
