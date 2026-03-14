"""Extratores da API de localidades do IBGE."""

from pathlib import Path

from extracao.publica.base import ExtratorAPIPublicaBase


class ExtratorLocalidadesIBGE(ExtratorAPIPublicaBase):
    """Baixa dimensões territoriais do IBGE para padronização de joins."""

    DATASETS = {
        "regioes": "/api/v1/localidades/regioes",
        "estados": "/api/v1/localidades/estados",
        "municipios": "/api/v1/localidades/municipios",
    }

    def __init__(self):
        """Configura a extração de localidades com taxa conservadora."""

        super().__init__(
            orgao="ibge",
            nome_endpoint="localidades",
            rate_limit_per_sec=3.0,
            max_rate_per_sec=6.0,
        )

    def executar(self, datasets: list[str] | None = None):
        """Extrai os datasets de localidades solicitados."""

        selecionados = datasets or list(self.DATASETS)

        for dataset in selecionados:
            endpoint = self.DATASETS[dataset]
            resumo = self._executar_tarefa_unica(
                endpoint=endpoint,
                params={},
                relative_output_path=Path("ibge") / "localidades" / f"{dataset}.json",
                context={"dataset": dataset},
            )

            self.logger.info(
                "[IBGE] Dataset concluido | dataset=%s | status=%s | registros=%s",
                dataset,
                resumo["status"],
                resumo["records"],
            )
