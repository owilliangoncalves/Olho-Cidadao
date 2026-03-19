"""Orquestra a pipeline principal de extração da Câmara dos Deputados."""

from configuracao.endpoint import obter_configuracao_endpoint
from configuracao.projeto import obter_parametros_pipeline
from configuracao.logger import logger
from extracao.camara.deputados_federais.dependente import ExtratorDependente
from extracao.camara.deputados_federais.deputados import ExtratorDeputadosLegislatura
from extracao.camara.deputados_federais.extrator_legislatura import ExtratorLegislaturas
from infra.errors import UserInputError
from utils.csv.despesas_deputados import ConversorDespesasCSV


class PipelineCamara:
    """Executa a cadeia completa de extração e consolidação da Câmara.

    O fluxo segue a dependência natural entre os dados:

    1. baixa a lista de legislaturas;
    2. extrai os deputados vinculados a cada legislatura;
    3. coleta as despesas por deputado e por ano;
    4. consolida os arquivos JSON Lines em um CSV analítico.

    Attributes:
        ano_inicio: Primeiro ano a ser considerado na etapa de despesas.
        ano_fim: Limite superior exclusivo da etapa de despesas.
    """

    def __init__(self, ano_inicio: int | None = None, ano_fim: int | None = None):
        """Armazena o intervalo de anos usado na extração de despesas."""

        config = obter_parametros_pipeline("camara")
        self.ano_inicio = ano_inicio if ano_inicio is not None else config.get("ano_inicio")
        self.ano_fim = ano_fim if ano_fim is not None else config.get("ano_fim")

    def _validar_precondicoes(self):
        """Falha cedo quando a configuração anual da Câmara é inválida."""

        if self.ano_inicio is None or self.ano_fim is None:
            raise UserInputError(
                "O pipeline da Camara exige ano_inicio e ano_fim. "
                "Defina [config.pipelines.camara] no etl-config.toml "
                "ou informe --ano-inicio/--ano-fim."
            )

        if self.ano_inicio >= self.ano_fim:
            raise UserInputError(
                "ano_inicio deve ser menor que ano_fim no pipeline da Camara."
            )

    def executar(self):
        """Executa todas as etapas do pipeline da Câmara em sequência."""

        logger.info("=== INICIANDO PIPELINE COMPLETO DA CÂMARA ===")
        self._validar_precondicoes()

        try:
            logger.info("--- Etapa 0: Extraindo lista de legislaturas ---")
            ExtratorLegislaturas().executar()

            logger.info("--- Etapa 1: Extraindo deputados por legislatura ---")
            ExtratorDeputadosLegislatura().executar()

            logger.info(
                "--- Etapa 2: Extraindo despesas (%s a %s) ---",
                self.ano_inicio,
                self.ano_fim - 1,
            )
            endpoint_despesas = "deputados_despesas"
            config_despesas = obter_configuracao_endpoint(endpoint_despesas)

            extrator_dep = ExtratorDependente(endpoint_despesas, config_despesas)
            extrator_dep.executar(ano_inicio=self.ano_inicio, ano_fim=self.ano_fim)

            logger.info("--- Etapa 3: Consolidando despesas em CSV ---")
            conversor_csv = ConversorDespesasCSV()
            conversor_csv.executar()

            logger.info("=== PIPELINE FINALIZADO COM SUCESSO ===")

        except Exception as exc:
            logger.exception("Pipeline interrompido devido a um erro: %s", exc)
            raise
