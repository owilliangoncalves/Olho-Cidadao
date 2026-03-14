"""Extratores da API de dados abertos do Siconfi."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from configuracao.projeto import obter_parametros_extrator
from extracao.publica.base import ExtratorAPIPublicaBase
from infra.errors import UserInputError
from utils.filtros import slug_filtros


@dataclass(frozen=True)
class SiconfiResourceSpec:
    """Define o contrato mínimo de um recurso do Siconfi."""

    path: str
    required_filters: tuple[str, ...] = ()
    aliases: dict[str, str] | None = None
    allowed_values: dict[str, frozenset] | None = None
    example_filters: tuple[str, ...] = ()


_COMMON_ALIASES = {
    "cod_ibge": "id_ente",
    "ano": "an_referencia",
    "ano_referencia": "an_referencia",
    "ano_exercicio": "an_exercicio",
    "mes": "me_referencia",
    "mes_referencia": "me_referencia",
    "tipo_matriz": "co_tipo_matriz",
    "tipo_valor": "id_tv",
}

SICONFI_RESOURCE_SPECS = {
    "entes": SiconfiResourceSpec(
        path="/entes",
        aliases={"cod_ibge": "id_ente"},
        example_filters=(),
    ),
    "extrato_entregas": SiconfiResourceSpec(
        path="/extrato_entregas",
        required_filters=("id_ente", "an_referencia"),
        aliases={
            **_COMMON_ALIASES,
            "exercicio": "an_referencia",
        },
        example_filters=("id_ente=3550308", "an_referencia=2024"),
    ),
    "msc_orcamentaria": SiconfiResourceSpec(
        path="/msc_orcamentaria",
        required_filters=(
            "id_ente",
            "an_referencia",
            "me_referencia",
            "co_tipo_matriz",
            "classe_conta",
            "id_tv",
        ),
        aliases={
            **_COMMON_ALIASES,
            "exercicio": "an_referencia",
        },
        allowed_values={
            "co_tipo_matriz": frozenset({"MSCC", "MSCE"}),
            "id_tv": frozenset({"beginning_balance", "ending_balance", "period_change"}),
        },
        example_filters=(
            "id_ente=3550308",
            "an_referencia=2024",
            "me_referencia=12",
            "co_tipo_matriz=MSCC",
            "classe_conta=6",
            "id_tv=period_change",
        ),
    ),
    "msc_controle": SiconfiResourceSpec(
        path="/msc_controle",
        required_filters=(
            "id_ente",
            "an_referencia",
            "me_referencia",
            "co_tipo_matriz",
            "classe_conta",
            "id_tv",
        ),
        aliases={
            **_COMMON_ALIASES,
            "exercicio": "an_referencia",
        },
        allowed_values={
            "co_tipo_matriz": frozenset({"MSCC", "MSCE"}),
            "id_tv": frozenset({"beginning_balance", "ending_balance", "period_change"}),
        },
        example_filters=(
            "id_ente=3550308",
            "an_referencia=2024",
            "me_referencia=12",
            "co_tipo_matriz=MSCC",
            "classe_conta=8",
            "id_tv=period_change",
        ),
    ),
    "msc_patrimonial": SiconfiResourceSpec(
        path="/msc_patrimonial",
        required_filters=(
            "id_ente",
            "an_referencia",
            "me_referencia",
            "co_tipo_matriz",
            "classe_conta",
            "id_tv",
        ),
        aliases={
            **_COMMON_ALIASES,
            "exercicio": "an_referencia",
        },
        allowed_values={
            "co_tipo_matriz": frozenset({"MSCC", "MSCE"}),
            "id_tv": frozenset({"beginning_balance", "ending_balance", "period_change"}),
        },
        example_filters=(
            "id_ente=3550308",
            "an_referencia=2024",
            "me_referencia=12",
            "co_tipo_matriz=MSCC",
            "classe_conta=1",
            "id_tv=period_change",
        ),
    ),
    "rreo": SiconfiResourceSpec(
        path="/rreo",
        required_filters=(
            "an_exercicio",
            "nr_periodo",
            "co_tipo_demonstrativo",
            "id_ente",
        ),
        aliases={
            **_COMMON_ALIASES,
            "exercicio": "an_exercicio",
        },
        example_filters=(
            "an_exercicio=2024",
            "nr_periodo=6",
            "co_tipo_demonstrativo=RREO",
            "id_ente=3550308",
        ),
    ),
    "rgf": SiconfiResourceSpec(
        path="/rgf",
        required_filters=(
            "an_exercicio",
            "in_periodicidade",
            "nr_periodo",
            "co_tipo_demonstrativo",
            "co_poder",
            "id_ente",
        ),
        aliases={
            **_COMMON_ALIASES,
            "exercicio": "an_exercicio",
            "periodicidade": "in_periodicidade",
            "poder": "co_poder",
            "esfera": "co_esfera",
        },
        allowed_values={
            "in_periodicidade": frozenset({"S", "Q"}),
        },
        example_filters=(
            "an_exercicio=2024",
            "in_periodicidade=Q",
            "nr_periodo=3",
            "co_tipo_demonstrativo=RGF",
            "co_poder=E",
            "id_ente=3550308",
        ),
    ),
    "dca": SiconfiResourceSpec(
        path="/dca",
        required_filters=("an_exercicio", "id_ente"),
        aliases={
            **_COMMON_ALIASES,
            "exercicio": "an_exercicio",
        },
        example_filters=("an_exercicio=2024", "id_ente=3550308"),
    ),
}

SICONFI_RESOURCES = {
    nome_recurso: spec.path for nome_recurso, spec in SICONFI_RESOURCE_SPECS.items()
}


class ExtratorSiconfi(ExtratorAPIPublicaBase):
    """Extrai datasets paginados da plataforma Siconfi."""

    def __init__(self, page_size: int | None = None):
        """Configura o crawler do Siconfi com paginação por offset."""

        config = obter_parametros_extrator("siconfi")
        super().__init__(
            orgao="siconfi",
            nome_endpoint="dados_abertos",
            rate_limit_per_sec=config.get("rate_limit_per_sec"),
            max_rate_per_sec=config.get("max_rate_per_sec"),
        )
        self.page_size = page_size if page_size is not None else config.get("page_size")
        self.required_meta_keys = {
            *self.required_meta_keys,
            "dataset",
            "filtros",
        }

    def _obter_spec(self, recurso: str) -> SiconfiResourceSpec:
        """Retorna a especificação declarativa de um recurso suportado."""

        try:
            return SICONFI_RESOURCE_SPECS[recurso]
        except KeyError as exc:
            raise UserInputError(
                f"Recurso Siconfi inválido '{recurso}'. "
                f"Use um dos recursos suportados: {', '.join(sorted(SICONFI_RESOURCES))}."
            ) from exc

    def _normalizar_chave_filtro(
        self,
        recurso: str,
        spec: SiconfiResourceSpec,
        chave: str,
    ) -> str:
        """Resolve aliases de filtros para o nome canônico aceito pela API."""

        aliases = spec.aliases or {}
        if chave in aliases:
            self.logger.debug(
                "[SICONFI] Normalizando filtro %s=%s para %s",
                recurso,
                chave,
                aliases[chave],
            )
        return aliases.get(chave, chave)

    def _normalizar_valor_filtro(self, chave: str, valor):
        """Ajusta caixa e formato de filtros com enum conhecido."""

        if not isinstance(valor, str):
            return valor

        valor = valor.strip()
        if chave in {"co_tipo_matriz", "co_tipo_demonstrativo", "in_periodicidade", "co_esfera", "co_poder"}:
            return valor.upper()
        if chave == "id_tv":
            return valor.lower()
        return valor

    def _normalizar_filtros_recurso(self, recurso: str, filtros: dict | None) -> dict:
        """Converte aliases e garante consistência entre chaves equivalentes."""

        spec = self._obter_spec(recurso)
        normalizados: dict = {}
        for chave, valor in (filtros or {}).items():
            chave_normalizada = self._normalizar_chave_filtro(recurso, spec, chave)
            valor_normalizado = self._normalizar_valor_filtro(chave_normalizada, valor)

            if (
                chave_normalizada in normalizados
                and normalizados[chave_normalizada] != valor_normalizado
            ):
                raise UserInputError(
                    f"Filtros conflitantes para o recurso '{recurso}': "
                    f"'{chave_normalizada}' recebeu valores diferentes "
                    f"({normalizados[chave_normalizada]!r} e {valor_normalizado!r})."
                )

            normalizados[chave_normalizada] = valor_normalizado

        return normalizados

    def _validar_filtros_recurso(self, recurso: str, filtros: dict):
        """Falha cedo quando a combinação de filtros não atende ao contrato mínimo."""

        spec = self._obter_spec(recurso)
        faltantes = [chave for chave in spec.required_filters if chave not in filtros]
        if faltantes:
            exemplo = ""
            if spec.example_filters:
                exemplo = (
                    " Exemplo: "
                    + " ".join(f"--filtro {filtro}" for filtro in spec.example_filters)
                )
            raise UserInputError(
                f"O recurso Siconfi '{recurso}' exige os filtros obrigatórios: "
                f"{', '.join(spec.required_filters)}. "
                f"Faltando: {', '.join(faltantes)}.{exemplo}"
            )

        allowed_values = spec.allowed_values or {}
        for chave, valores_permitidos in allowed_values.items():
            if chave not in filtros:
                continue
            if filtros[chave] not in valores_permitidos:
                raise UserInputError(
                    f"Filtro inválido para o recurso '{recurso}': "
                    f"{chave}={filtros[chave]!r}. "
                    f"Valores aceitos: {', '.join(map(str, sorted(valores_permitidos)))}."
                )

        classe_conta = filtros.get("classe_conta")
        if classe_conta is not None:
            classes_por_recurso = {
                "msc_orcamentaria": {5, 6},
                "msc_controle": {7, 8},
                "msc_patrimonial": {1, 2, 3, 4},
            }
            valores_permitidos = classes_por_recurso.get(recurso)
            if valores_permitidos and classe_conta not in valores_permitidos:
                raise UserInputError(
                    f"Filtro inválido para o recurso '{recurso}': "
                    f"classe_conta={classe_conta!r}. "
                    f"Valores aceitos: {', '.join(map(str, sorted(valores_permitidos)))}."
                )

        mes_referencia = filtros.get("me_referencia")
        if mes_referencia is not None and not 1 <= int(mes_referencia) <= 12:
            raise UserInputError(
                "Filtro inválido para o Siconfi: me_referencia deve estar entre 1 e 12."
            )

    def executar(self, recursos: list[str] | None = None, filtros: dict | None = None):
        """Extrai os recursos desejados do Siconfi."""

        recursos_selecionados = recursos or ["entes"]

        for recurso in recursos_selecionados:
            spec = self._obter_spec(recurso)
            filtros_recurso = self._normalizar_filtros_recurso(recurso, filtros)
            self._validar_filtros_recurso(recurso, filtros_recurso)
            assinatura = slug_filtros(filtros_recurso)
            resumo = self._executar_tarefa_paginada(
                endpoint=spec.path,
                base_params=filtros_recurso,
                relative_output_path=(
                    Path("siconfi")
                    / recurso
                    / f"consulta={assinatura}.json"
                ),
                context={
                    "dataset": recurso,
                    "filtros": filtros_recurso,
                },
                pagination={
                    "style": "offset",
                    "offset_param": "offset",
                    "limit_param": "limit",
                    "page_size": self.page_size,
                    "start_offset": 0,
                },
                item_keys=("items", "data"),
            )

            self.logger.info(
                "[SICONFI] Recurso concluido | recurso=%s | status=%s | registros=%s",
                recurso,
                resumo["status"],
                resumo["records"],
            )
