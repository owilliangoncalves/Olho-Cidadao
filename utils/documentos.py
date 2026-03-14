"""Funções utilitárias para normalização de CPF e CNPJ."""

import re


def somente_digitos(valor) -> str:
    """Remove qualquer caractere não numérico do valor informado."""

    if valor is None:
        return ""
    return re.sub(r"\D", "", str(valor))


def normalizar_documento(valor) -> str | None:
    """Normaliza um CPF/CNPJ e valida o tamanho mínimo esperado.

    Args:
        valor: Valor bruto recebido da fonte de dados.

    Returns:
        Documento contendo apenas dígitos quando o tamanho é compatível com
        CPF ou CNPJ. Retorna `None` para valores vazios ou inválidos.
    """

    documento = somente_digitos(valor)
    if len(documento) not in {11, 14}:
        return None
    return documento


def tipo_documento(documento: str | None) -> str | None:
    """Classifica um documento normalizado como CPF ou CNPJ."""

    if documento is None:
        return None
    if len(documento) == 11:
        return "cpf"
    if len(documento) == 14:
        return "cnpj"
    return None


def base_cnpj(documento: str | None) -> str | None:
    """Retorna a raiz do CNPJ quando o documento informado for um CNPJ."""

    if documento is None or len(documento) != 14:
        return None
    return documento[:8]
