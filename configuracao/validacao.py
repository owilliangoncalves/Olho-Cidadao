from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date
from typing import Any, TypeVar, cast, get_args, get_origin

from configuracao.excecoes import ConfiguracaoInvalida
from configuracao.modelos import (
    CliIntervaloAnosConfig,
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
            # tipo_esperado é Any, mas we know it's a dataclass type
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
    for f in fields(cast(Any, cls)):
        if f.name not in data:
            continue
        kwargs[f.name] = _validar_tipo_basico(data[f.name], f.type, f"{caminho}.{f.name}")

    obj: T = cls(**kwargs)  # type: ignore[assignment]

    # Type narrowing: usar isinstance para validação, não para type checking
    if isinstance(obj, EndpointConfig):
        validar_endpoint(obj, caminho)
    elif isinstance(obj, PipelineConfig):
        validar_pipeline(obj, caminho)
    elif isinstance(obj, CliIntervaloAnosConfig):
        validar_intervalo_anos(obj, caminho)

    return obj


def validar_endpoint(cfg: EndpointConfig, caminho: str) -> None:
    # cfg.endpoint já é str por contrato de dataclass, cfg.itens é int, cfg.campo_id é str
    if not cfg.endpoint:
        raise ConfiguracaoInvalida(f"'{caminho}.endpoint' deve ser uma string não vazia.")
    if cfg.itens <= 0:
        raise ConfiguracaoInvalida(f"'{caminho}.itens' deve ser maior que zero.")
    if not cfg.campo_id.strip():
        raise ConfiguracaoInvalida(f"'{caminho}.campo_id' não pode ser vazio.")


def validar_pipeline(cfg: PipelineConfig, caminho: str) -> None:
    # cfg.etapas já é list[str] por contrato de dataclass
    if any(not etapa.strip() for etapa in cfg.etapas):
        raise ConfiguracaoInvalida(f"'{caminho}.etapas' deve conter apenas strings não vazias.")


def validar_intervalo_anos(cfg: CliIntervaloAnosConfig, caminho: str) -> None:
    # cfg.inicio e cfg.fim já são date | str | None por contrato de dataclass
    for nome, valor in (("inicio", cfg.inicio), ("fim", cfg.fim)):
        if valor is not None:
            # Type narrowing: valor é date | str aqui
            pass


def construir_config_projeto(raw: dict[str, Any]) -> ProjetoConfig:
    # Extract and typenar em uma única passagem
    def _get_dict(d: Any, key: str) -> dict[str, Any]:
        value = d.get(key, {}) if isinstance(d, dict) else {}
        if not isinstance(value, dict):
            raise ConfiguracaoInvalida(f"'{key}' deve ser uma tabela TOML.")
        return value

    endpoints_raw = _get_dict(raw, "endpoints")
    pipelines_raw = _get_dict(raw, "pipelines")
    config_raw = _get_dict(raw, "config")

    endpoints: dict[str, EndpointConfig] = {
        nome: construir_dataclass(EndpointConfig, valor, f"endpoints.{nome}")
        for nome, valor in endpoints_raw.items()
    }

    pipelines: dict[str, PipelineConfig] = {
        nome: construir_dataclass(PipelineConfig, valor, f"pipelines.{nome}")
        for nome, valor in pipelines_raw.items()
    }

    cli_cfg = _get_dict(config_raw, "cli")
    extratores_cfg = _get_dict(config_raw, "extratores")
    pipelines_cfg = _get_dict(config_raw, "pipelines")

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