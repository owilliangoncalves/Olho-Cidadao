from pathlib import Path

from configuracao.logger import logger
from utils.csv.atas_pncp import ConversorAtasPNCPCSV
from utils.csv.despesas_deputados import ConversorDespesasCSV
from utils.csv.estados_ibge import ConversorEstadosIBGECSV
from utils.csv.extrair_deputados_legislatura import ConversorDeputadosLegislaturaCSV
from utils.csv.extrair_legislaturas import ConversorLegislaturasCSV
from utils.csv.fornecedores_portal import ConversorFornecedoresPortalCSV
from utils.csv.municipios_ibge import ConversorMunicipiosIBGECSV
from utils.csv.orcamento_item_despesa_particoes_siop import (
    ConversorParticoesOrcamentoItemDespesaSIOPCSV,
)
from utils.csv.orcamento_item_despesa_siop import ConversorOrcamentoItemDespesaSIOPCSV
from utils.csv.regioes_ibge import ConversorRegioesIBGECSV


class OrquestradorGeracaoCSVs:
    """Executa, em sequência, todos os geradores de CSV do projeto."""

    GERADORES_CSV = (
        ("despesas", ConversorDespesasCSV, Path("despesas")),
        ("legislaturas", ConversorLegislaturasCSV, Path("legislaturas")),
        ("deputados_legislatura", ConversorDeputadosLegislaturaCSV, Path("deputados_legislatura")),
        ("ibge_regioes", ConversorRegioesIBGECSV, Path("ibge")),
        ("ibge_estados", ConversorEstadosIBGECSV, Path("ibge")),
        ("ibge_municipios", ConversorMunicipiosIBGECSV, Path("ibge")),
        ("siop_orcamento_item_despesa", ConversorOrcamentoItemDespesaSIOPCSV, Path("siop") / "orcamento_item_despesa"),
        (
            "siop_orcamento_item_despesa_particoes",
            ConversorParticoesOrcamentoItemDespesaSIOPCSV,
            Path("siop") / "orcamento_item_despesa_particoes",
        ),
        ("pncp_atas", ConversorAtasPNCPCSV, Path("pncp") / "atas"),
        ("portal_dim_fornecedores", ConversorFornecedoresPortalCSV, Path("portal_transparencia") / "dimensoes"),
    )

    def __init__(self, data_dir: str = "data", output_dir: str = "data/csv", log_dir: str = "logs"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.log_dir = Path(log_dir)

    def executar(self) -> list[str]:
        """Instancia e executa todos os geradores registrados."""

        executados = []
        logger.info("=== INICIANDO ORQUESTRACAO DE GERACAO DE CSVS ===")

        for nome, classe_gerador, subdiretorio_saida in self.GERADORES_CSV:
            logger.info("--- Gerando CSVs: %s ---", nome)
            gerador = classe_gerador(
                data_dir=str(self.data_dir),
                output_dir=str(self.output_dir / subdiretorio_saida),
                log_dir=str(self.log_dir),
            )
            gerador.executar()
            executados.append(nome)

        logger.info("=== ORQUESTRACAO DE CSVS FINALIZADA | geradores=%s ===", len(executados))
        return executados
