"""Validação tipada do `etl-config.toml` e construção do schema do projeto."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date
from typing import Any, TypeVar, cast, get_args, get_origin, get_type_hints

from configuracao.excecoes import ConfiguracaoInvalida
from configuracao.modelos import (
    ConfigOperacional,
    EndpointConfig,
    PipelineConfig,
    ProjetoConfig,
)

T = TypeVar("T")


def _esperado(tipo: Any) -> str:
    try:
        return str(tipo)
    except Exception:
        return repr(tipo)


def _validar_tipo_basico(valor: Any, tipo_esperado: Any, caminho: str) -> Any:
    if tipo_esperado is Any:
        return valor

    origin: Any = get_origin(tipo_esperado)
    args: tuple[Any, ...] = get_args(tipo_esperado)

    if origin is None:
        if tipo_esperado is date:
            if isinstance(valor, (date, str)) or valor is None:
                return valor
            raise ConfiguracaoInvalida(
                f"Campo '{caminho}' deve ser date | str | None, recebido: {type(valor).__name__}."
            )

        if is_dataclass(tipo_esperado):
            if not isinstance(valor, dict):
                raise ConfiguracaoInvalida(
                    f"Campo '{caminho}' deve ser um objeto/dict, recebido: {type(valor).__name__}."
                )
            return construir_dataclass(cast(type[Any], tipo_esperado), valor, caminho)

        if not isinstance(valor, tipo_esperado):
            raise ConfiguracaoInvalida(
                f"Campo '{caminho}' deve ser {_esperado(tipo_esperado)}, "
                f"recebido: {type(valor).__name__}."
            )
        return valor

    if origin is list:
        if not isinstance(valor, list):
            raise ConfiguracaoInvalida(
                f"Campo '{caminho}' deve ser list, recebido: {type(valor).__name__}."
            )
        item_type: Any = args[0] if args else Any
        lista: list[Any] = valor
        return [
            _validar_tipo_basico(item, item_type, f"{caminho}[{i}]")
            for i, item in enumerate(lista)
        ]

    if origin is dict:
        if not isinstance(valor, dict):
            raise ConfiguracaoInvalida(
                f"Campo '{caminho}' deve ser dict, recebido: {type(valor).__name__}."
            )
        _, value_type = args if len(args) == 2 else (Any, Any)
        dicio: dict[Any, Any] = valor
        return {
            str(k): _validar_tipo_basico(v, value_type, f"{caminho}.{k}")
            for k, v in dicio.items()
        }

    if str(origin).endswith("UnionType") or str(origin) == "typing.Union":
        for possible_type in args:
            if possible_type is type(None) and valor is None:
                return valor
            try:
                return _validar_tipo_basico(valor, possible_type, caminho)
            except ConfiguracaoInvalida:
                pass
        raise ConfiguracaoInvalida(
            f"Campo '{caminho}' inválido. Esperado um dos tipos {_esperado(args)}, "
            f"recebido: {type(valor).__name__}."
        )

    return valor


def construir_dataclass(cls: type[T], data: dict[str, Any], caminho: str = "root") -> T:
    if not isinstance(data, dict):
        raise ConfiguracaoInvalida(
            f"Esperado dict para '{caminho}', recebido: {type(data).__name__}."
        )

    allowed = {f.name for f in fields(cast(Any, cls))}
    unknown = set(data.keys()) - allowed
    if unknown:
        raise ConfiguracaoInvalida(
            f"Campos desconhecidos em '{caminho}': {', '.join(sorted(unknown))}."
        )

    kwargs: dict[str, Any] = {}
    type_hints = get_type_hints(cls)
    for f in fields(cast(Any, cls)):
        if f.name not in data:
            continue
        tipo_campo = type_hints.get(f.name, f.type)
        kwargs[f.name] = _validar_tipo_basico(data[f.name], tipo_campo, f"{caminho}.{f.name}")

    obj: T = cls(**kwargs)  # type: ignore[assignment]

    if isinstance(obj, EndpointConfig):
        validar_endpoint(obj, caminho)
    elif isinstance(obj, PipelineConfig):
        validar_pipeline(obj, caminho)

    return obj


def validar_endpoint(cfg: EndpointConfig, caminho: str) -> None:
    if not cfg.endpoint:
        raise ConfiguracaoInvalida(f"'{caminho}.endpoint' deve ser uma string não vazia.")
    if cfg.itens <= 0:
        raise ConfiguracaoInvalida(f"'{caminho}.itens' deve ser maior que zero.")
    if not cfg.campo_id.strip():
        raise ConfiguracaoInvalida(f"'{caminho}.campo_id' não pode ser vazio.")
    if cfg.salvar_como is not None and not cfg.salvar_como.strip():
        raise ConfiguracaoInvalida(f"'{caminho}.salvar_como' não pode ser vazio.")
    if cfg.ano_inicio is not None and cfg.ano_fim is not None and cfg.ano_inicio > cfg.ano_fim:
        raise ConfiguracaoInvalida(f"'{caminho}' deve ter ano_inicio <= ano_fim.")
    if any(not isinstance(fase, int) for fase in cfg.fases):
        raise ConfiguracaoInvalida(f"'{caminho}.fases' deve conter apenas inteiros.")


def validar_pipeline(cfg: PipelineConfig, caminho: str) -> None:
    if any(not etapa.strip() for etapa in cfg.etapas):
        raise ConfiguracaoInvalida(f"'{caminho}.etapas' deve conter apenas strings não vazias.")
    if cfg.max_workers is not None and cfg.max_workers <= 0:
        raise ConfiguracaoInvalida(f"'{caminho}.max_workers' deve ser maior que zero.")
    if cfg.ano_inicio is not None and cfg.ano_fim is not None and cfg.ano_inicio >= cfg.ano_fim:
        raise ConfiguracaoInvalida(f"'{caminho}' deve ter ano_inicio < ano_fim.")


def _obter_tabela(dados: Any, chave: str) -> dict[str, Any]:
    """Lê uma tabela TOML obrigatoriamente como `dict`."""

    valor = dados.get(chave, {}) if isinstance(dados, dict) else {}
    if not isinstance(valor, dict):
        raise ConfiguracaoInvalida(f"'{chave}' deve ser uma tabela TOML.")
    return valor


def construir_config_projeto(raw: dict[str, Any]) -> ProjetoConfig:
    """Constrói o objeto tipado raiz do projeto a partir do TOML cru."""

    endpoints_raw = _obter_tabela(raw, "endpoints")
    pipelines_raw = _obter_tabela(raw, "pipelines")
    config_raw = _obter_tabela(raw, "config")

    endpoints: dict[str, EndpointConfig] = {
        nome: construir_dataclass(EndpointConfig, valor, f"endpoints.{nome}")
        for nome, valor in endpoints_raw.items()
    }

    pipelines: dict[str, PipelineConfig] = {
        nome: construir_dataclass(PipelineConfig, valor, f"pipelines.{nome}")
        for nome, valor in pipelines_raw.items()
    }

    cli_cfg = _obter_tabela(config_raw, "cli")
    extratores_cfg = _obter_tabela(config_raw, "extratores")
    pipelines_cfg = _obter_tabela(config_raw, "pipelines")

    config = ConfigOperacional(
        cli=cli_cfg,
        extratores=extratores_cfg,
        pipelines=pipelines_cfg,
    )

    return ProjetoConfig(
        endpoints=endpoints,
        pipelines=pipelines,
        config=config,
    )
