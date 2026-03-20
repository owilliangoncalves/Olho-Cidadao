"""Configuração operacional do pacote de deputados federais da Câmara."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from configuracao import obter_configuracao_endpoint
from configuracao import obter_parametros_extrator

LEGISLATURAS_REQUIRED_KEYS = frozenset({"id", "dataInicio", "dataFim"})
DEPUTADOS_REQUIRED_KEYS = frozenset({"id", "id_legislatura"})
DESPESAS_REQUIRED_KEYS = frozenset(
    {
        "documento_fornecedor_normalizado",
        "tipo_documento_fornecedor",
        "cnpj_base_fornecedor",
        "orgao_origem",
        "endpoint_origem",
        "id_legislatura",
        "nome_deputado",
        "uri_deputado",
        "sigla_uf_deputado",
        "sigla_partido_deputado",
    }
)


def _resolver_caminho_dados(valor: str | Path) -> Path:
    """Normaliza caminhos relativos para a raiz `data/` do projeto."""

    caminho = Path(valor)
    if caminho.is_absolute() or caminho.parts[:1] == ("data",):
        return caminho
    return Path("data") / caminho


@dataclass(frozen=True)
class LegislaturasConfig:
    """Configuração do extrator da lista mestre de legislaturas."""

    endpoint: str
    itens: int
    arquivo_saida: Path

    @classmethod
    def carregar(cls, arquivo_saida: str | None = None) -> "LegislaturasConfig":
        endpoint_cfg = obter_configuracao_endpoint("legislaturas")
        extrator_cfg = obter_parametros_extrator("camara.legislaturas")
        return cls(
            endpoint=endpoint_cfg["endpoint"],
            itens=int(endpoint_cfg["itens"]),
            arquivo_saida=_resolver_caminho_dados(
                arquivo_saida
                or extrator_cfg.get("arquivo_saida")
                or endpoint_cfg["salvar_como"]
            ),
        )


@dataclass(frozen=True)
class DeputadosLegislaturaConfig:
    """Configuração do extrator de deputados por legislatura."""

    endpoint: str
    itens: int
    arquivo_entrada: Path
    pasta_saida: Path
    prefixo_arquivo: str
    max_workers: int

    @property
    def max_pending(self) -> int:
        """Deriva a janela local de futures a partir do paralelismo."""

        return self.max_workers * 4

    @classmethod
    def carregar(
        cls,
        arquivo_entrada: str | None = None,
        pasta_saida: str | None = None,
        prefixo_arquivo: str | None = None,
    ) -> "DeputadosLegislaturaConfig":
        endpoint_cfg = obter_configuracao_endpoint("deputados")
        extrator_cfg = obter_parametros_extrator("camara.deputados_legislatura")
        return cls(
            endpoint=endpoint_cfg["endpoint"],
            itens=int(endpoint_cfg["itens"]),
            arquivo_entrada=_resolver_caminho_dados(
                arquivo_entrada or extrator_cfg.get("arquivo_entrada")
            ),
            pasta_saida=_resolver_caminho_dados(
                pasta_saida or extrator_cfg.get("pasta_saida")
            ),
            prefixo_arquivo=prefixo_arquivo or extrator_cfg.get("prefixo_arquivo"),
            max_workers=int(extrator_cfg.get("max_workers") or 1),
        )


@dataclass(frozen=True)
class DespesasConfig:
    """Configuração do extrator dependente de despesas por deputado."""

    nome_endpoint: str
    endpoint_template: str
    endpoint_pai: str
    campo_id: str
    pasta_dados: Path
    max_workers: int
    rate_limit_per_sec: float | None
    max_rate_per_sec: float | None

    @property
    def max_pending(self) -> int:
        """Deriva a fila máxima local sem duplicar estado."""

        return self.max_workers * 4

    @classmethod
    def carregar(
        cls,
        nome_endpoint: str,
        configuracao: dict,
        *,
        pasta_dados: str | Path = "data",
    ) -> "DespesasConfig":
        extrator_cfg = obter_parametros_extrator(f"camara.{nome_endpoint}")
        return cls(
            nome_endpoint=nome_endpoint,
            endpoint_template=configuracao["endpoint"],
            endpoint_pai=configuracao["depende_de"],
            campo_id=configuracao.get("campo_id", "id"),
            pasta_dados=_resolver_caminho_dados(pasta_dados),
            max_workers=int(extrator_cfg.get("max_workers") or 8),
            rate_limit_per_sec=extrator_cfg.get("rate_limit_per_sec"),
            max_rate_per_sec=extrator_cfg.get("max_rate_per_sec"),
        )
