//! Configuração de leitura dos artefatos de dados do `Olho Cidadão`.
//!
//! Este módulo resolve os caminhos físicos usados pelo backend para localizar
//! os arquivos produzidos pelo ETL. A ideia é manter a camada de serviço
//! desacoplada de caminhos hardcoded e de diferenças entre ambientes.

mod citizen_data_config;
mod citizen_data_limits;
mod citizen_data_paths;
mod resolve_relative;

pub use self::citizen_data_config::CitizenDataConfig;
pub use self::citizen_data_limits::CitizenDataLimits;
pub use self::citizen_data_paths::CitizenDataPaths;
