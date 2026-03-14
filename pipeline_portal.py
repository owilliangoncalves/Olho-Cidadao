"""Orquestra o enriquecimento do projeto com a API do Portal da Transparência."""

from configuracao.endpoint import obter_configuracao_endpoint
from configuracao.logger import logger
from configuracao.projeto import obter_parametros_pipeline
from extracao.portal.documentos_favorecido import ExtratorDocumentosPorFavorecidoPortal
from extracao.portal.fornecedores import ConstrutorDimFornecedoresPortal
from extracao.portal.notas_fiscais import ExtratorNotasFiscaisPortal
from extracao.portal.sancoes import ExtratorSancoesPortal
from infra.errors import UserInputError


class PipelinePortalTransparencia:
    """Coordena a construção da dimensão de fornecedores e seus enriquecimentos.

    O pipeline do Portal foi desenhado como uma camada complementar às extrações
    da Câmara e do Senado. Primeiro ele consolida uma dimensão local de
    fornecedores e, a partir dela, agenda consultas pontuais para os endpoints
    mais relevantes da API.
    """

    def __init__(
        self,
        limit_fornecedores: int | None = None,
        min_ocorrencias: int | None = None,
        ano_inicio: int | None = None,
        ano_fim: int | None = None,
        fases: list[int] | None = None,
    ):
        """Configura os filtros usados na construção das tarefas do Portal."""

        config = obter_parametros_pipeline("portal")
        self.limit_fornecedores = limit_fornecedores
        self.min_ocorrencias = (
            min_ocorrencias if min_ocorrencias is not None else config.get("min_ocorrencias")
        )
        self.ano_inicio = ano_inicio
        self.ano_fim = ano_fim
        self.fases = fases or config.get("fases")

        self.builder = ConstrutorDimFornecedoresPortal()
        self._validar_intervalo_anos()

    def _validar_intervalo_anos(self):
        """Falha cedo quando o recorte anual do Portal é incoerente."""

        if (
            self.ano_inicio is not None
            and self.ano_fim is not None
            and self.ano_inicio >= self.ano_fim
        ):
            raise UserInputError(
                "ano_inicio deve ser menor que ano_fim no pipeline do Portal."
            )

    def _validar_fases_documentos(self):
        """Garante que a configuração de fases é válida para documentos."""

        if not self.fases:
            raise UserInputError(
                "O pipeline do Portal exige ao menos uma fase em "
                "[config.pipelines.portal].fases ou via --fases."
            )

        if any(not isinstance(fase, int) or fase <= 0 for fase in self.fases):
            raise UserInputError(
                "As fases do pipeline do Portal devem ser inteiros positivos."
            )

    def _carregar_fornecedores(self):
        """Constrói e carrega a dimensão de fornecedores a ser enriquecida."""

        self.builder.construir(min_ocorrencias=self.min_ocorrencias)
        fornecedores = self.builder.carregar()

        if self.limit_fornecedores is not None:
            fornecedores = fornecedores[: self.limit_fornecedores]

        return fornecedores

    def _filtrar_anos(self, anos: list[int]) -> list[int]:
        """Aplica o recorte de anos configurado sobre a lista informada."""

        filtrados = []
        for ano in anos:
            if self.ano_inicio is not None and ano < self.ano_inicio:
                continue
            if self.ano_fim is not None and ano >= self.ano_fim:
                continue
            filtrados.append(ano)
        return filtrados

    def _gerar_tarefas_documentos(self, fornecedores):
        """Expande fornecedores em tarefas `(documento, ano, fase)`."""

        tarefas = []
        for fornecedor in fornecedores:
            documento = fornecedor["documento"]
            anos = self._filtrar_anos(fornecedor.get("anos", []))

            for ano in anos:
                for fase in self.fases:
                    tarefas.append((documento, ano, fase))

        tarefas.sort(key=lambda item: (item[1], item[2], item[0]), reverse=True)
        return tarefas

    def executar_dimensao(self):
        """Reconstrói a dimensão local de fornecedores."""

        return self.builder.construir(min_ocorrencias=self.min_ocorrencias)

    def executar_documentos(self):
        """Extrai o detalhamento de documentos por favorecido."""

        self._validar_fases_documentos()
        fornecedores = self._carregar_fornecedores()
        tarefas = self._gerar_tarefas_documentos(fornecedores)

        if not tarefas:
            logger.warning("[PORTAL] Nenhuma tarefa de documentos por favorecido foi gerada.")
            return

        config = obter_configuracao_endpoint("portal_documentos_favorecido")
        extrator = ExtratorDocumentosPorFavorecidoPortal(config["endpoint"])
        extrator.executar(tarefas)

    def executar_sancoes(self):
        """Consulta CEIS, CNEP e CEPIM para os fornecedores selecionados."""

        fornecedores = self._carregar_fornecedores()
        documentos = [item["documento"] for item in fornecedores]

        if not documentos:
            logger.warning("[PORTAL] Nenhum fornecedor disponivel para extrair sancoes.")
            return

        endpoints = {
            "ceis": obter_configuracao_endpoint("portal_ceis")["endpoint"],
            "cnep": obter_configuracao_endpoint("portal_cnep")["endpoint"],
            "cepim": obter_configuracao_endpoint("portal_cepim")["endpoint"],
        }

        extrator = ExtratorSancoesPortal(endpoints)
        extrator.executar(documentos)

    def executar_notas_fiscais(self):
        """Consulta notas fiscais emitidas pelos fornecedores selecionados."""

        fornecedores = self._carregar_fornecedores()
        documentos = [item["documento"] for item in fornecedores]

        if not documentos:
            logger.warning("[PORTAL] Nenhum fornecedor disponivel para extrair notas fiscais.")
            return

        config = obter_configuracao_endpoint("portal_notas_fiscais")
        extrator = ExtratorNotasFiscaisPortal(config["endpoint"])
        extrator.executar(documentos)

    def executar(self):
        """Executa todas as etapas do pipeline do Portal da Transparência."""

        logger.info("=== INICIANDO PIPELINE DO PORTAL DA TRANSPARENCIA ===")

        self.executar_dimensao()
        self.executar_documentos()
        self.executar_sancoes()
        self.executar_notas_fiscais()

        logger.info("=== PIPELINE DO PORTAL DA TRANSPARENCIA FINALIZADO ===")
