"""Menu interativo em terminal para navegação das funcionalidades da CLI."""

from __future__ import annotations

import shutil
import select
import subprocess
import sys
import termios
import textwrap
import threading
import time
import tty
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from configuracao.logger import LOG_FILE
from configuracao import obter_intervalo_anos_padrao
from configuracao import obter_parametros_cli

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_AMBER = "\033[38;5;214m"
_BLUE = "\033[38;5;75m"
_GREEN = "\033[38;5;78m"
_RED = "\033[38;5;203m"
_CYAN = "\033[38;5;87m"
_TEAL = "\033[38;5;44m"
_MAGENTA = "\033[38;5;176m"
_VIOLET = "\033[38;5;141m"
_PINK = "\033[38;5;212m"
_YELLOW = "\033[38;5;221m"
_LIME = "\033[38;5;118m"
_ORANGE = "\033[38;5;208m"
_MUTED = "\033[38;5;245m"
_PANEL = "\033[38;5;240m"
_SOFT = "\033[38;5;252m"
_SLATE = "\033[38;5;238m"
_CLEAR = "\033[2J\033[H"
_HOME = "\033[H"
_ALT_SCREEN_ON = "\033[?1049h"
_ALT_SCREEN_OFF = "\033[?1049l"
_HIDE_CURSOR = "\033[?25l"
_SHOW_CURSOR = "\033[?25h"
_CANCELLED = object()
_SPINNER = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


@dataclass(frozen=True)
class MenuItem:
    """Representa uma entrada navegável do menu interativo."""

    title: str
    description: str
    preview: str
    command_builder: Callable[[], list[str] | None] | None = None
    children: tuple["MenuItem", ...] = ()
    tags: tuple[str, ...] = ()
    interactive: bool = False
    icon: str = "•"
    accent: str = "default"

    @property
    def is_leaf(self) -> bool:
        """Indica se a entrada executa um comando diretamente."""

        return self.command_builder is not None


@dataclass
class MenuState:
    """Mantém o estado de navegação do dashboard de terminal."""

    category_index: int = 0
    item_index: int = 0
    focus: str = "items"
    query: str = ""
    category_item_indices: dict[int, int] | None = None
    pending_prefix: str = ""

    def __post_init__(self):
        if self.category_item_indices is None:
            self.category_item_indices = {}


@dataclass
class ExecutionResult:
    """Representa o estado final de um comando executado pelo menu."""

    status: str = "running"
    error_message: str | None = None
    exit_code: int | None = None


def _prompt_text(
    label: str,
    *,
    default: str | None = None,
    required: bool = False,
) -> str | None | object:
    """Lê um valor textual com suporte a default e cancelamento."""

    while True:
        suffix = " [q para cancelar]"
        if default not in (None, ""):
            suffix = f" [{default}; q para cancelar]"
        valor = input(f"{label}{suffix}: ").strip()
        if valor.lower() == "q":
            return _CANCELLED
        if not valor:
            if default not in (None, ""):
                return default
            if not required:
                return None
            print("Valor obrigatorio.")
            continue
        return valor


def _prompt_int(
    label: str,
    *,
    default: int | None = None,
    required: bool = False,
) -> int | None | object:
    """Lê um inteiro com suporte a default e cancelamento."""

    while True:
        bruto = _prompt_text(
            label,
            default=str(default) if default is not None else None,
            required=required,
        )
        if bruto is _CANCELLED:
            return _CANCELLED
        if bruto is None:
            return None
        try:
            return int(bruto)
        except ValueError:
            print("Informe um numero inteiro valido.")


def _build_static(command: str) -> Callable[[], list[str]]:
    """Cria um builder simples para comandos sem prompts adicionais."""

    return lambda: [command]


def _build_extrair_dependentes() -> list[str] | None:
    """Monta os argumentos do extrator dependente da Câmara."""

    intervalo = obter_intervalo_anos_padrao()
    endpoint = _prompt_text(
        "Endpoint da Camara",
        default="deputados_despesas",
        required=True,
    )
    if endpoint is _CANCELLED:
        return None

    ano_inicio = _prompt_int(
        "Ano inicio",
        default=intervalo.get("ano_inicio"),
        required=False,
    )
    if ano_inicio is None and intervalo.get("ano_inicio") is None:
        return None
    if ano_inicio is _CANCELLED:
        return None

    ano_fim = _prompt_int(
        "Ano fim exclusivo",
        default=intervalo.get("ano_fim"),
        required=False,
    )
    if ano_fim is _CANCELLED:
        return None
    if ano_fim is None and intervalo.get("ano_fim") is None:
        return None

    tokens = ["extrair-dependentes", "--endpoint", endpoint]
    if ano_inicio is not None:
        tokens.extend(["--ano-inicio", str(ano_inicio)])
    if ano_fim is not None:
        tokens.extend(["--ano-fim", str(ano_fim)])
    return tokens


def _build_portal_fornecedores() -> list[str] | None:
    """Monta os argumentos da dimensão de fornecedores do Portal."""

    config = obter_parametros_cli("portal")
    min_ocorrencias = _prompt_int(
        "Minimo de ocorrencias",
        default=config.get("min_ocorrencias"),
        required=False,
    )
    if min_ocorrencias is _CANCELLED:
        return None
    if min_ocorrencias is None and config.get("min_ocorrencias") is None:
        return None

    tokens = ["portal-construir-fornecedores"]
    if min_ocorrencias is not None:
        tokens.extend(["--min-ocorrencias", str(min_ocorrencias)])
    return tokens


def _build_portal_sancoes() -> list[str] | None:
    """Monta os argumentos do extrator de sanções do Portal."""

    config = obter_parametros_cli("portal")
    min_ocorrencias = _prompt_int(
        "Minimo de ocorrencias",
        default=config.get("min_ocorrencias"),
        required=False,
    )
    if min_ocorrencias is _CANCELLED:
        return None
    if min_ocorrencias is None and config.get("min_ocorrencias") is None:
        return None

    limit_fornecedores = _prompt_int(
        "Limite de fornecedores (Enter para usar todos)",
        default=None,
        required=False,
    )
    if limit_fornecedores is _CANCELLED:
        return None

    tokens = ["extrair-portal-sancoes"]
    if min_ocorrencias is not None:
        tokens.extend(["--min-ocorrencias", str(min_ocorrencias)])
    if limit_fornecedores is not None:
        tokens.extend(["--limit-fornecedores", str(limit_fornecedores)])
    return tokens


def _build_portal_notas() -> list[str] | None:
    """Monta os argumentos do extrator de notas fiscais do Portal."""

    config = obter_parametros_cli("portal")
    min_ocorrencias = _prompt_int(
        "Minimo de ocorrencias",
        default=config.get("min_ocorrencias"),
        required=False,
    )
    if min_ocorrencias is _CANCELLED:
        return None
    if min_ocorrencias is None and config.get("min_ocorrencias") is None:
        return None

    limit_fornecedores = _prompt_int(
        "Limite de fornecedores (Enter para usar todos)",
        default=None,
        required=False,
    )
    if limit_fornecedores is _CANCELLED:
        return None

    tokens = ["extrair-portal-notas-fiscais"]
    if min_ocorrencias is not None:
        tokens.extend(["--min-ocorrencias", str(min_ocorrencias)])
    if limit_fornecedores is not None:
        tokens.extend(["--limit-fornecedores", str(limit_fornecedores)])
    return tokens


def _build_portal_documentos() -> list[str] | None:
    """Monta os argumentos do extrator de documentos do Portal."""

    config = obter_parametros_cli("portal")
    min_ocorrencias = _prompt_int(
        "Minimo de ocorrencias",
        default=config.get("min_ocorrencias"),
        required=False,
    )
    if min_ocorrencias is _CANCELLED:
        return None
    if min_ocorrencias is None and config.get("min_ocorrencias") is None:
        return None

    limit_fornecedores = _prompt_int(
        "Limite de fornecedores (Enter para usar todos)",
        default=None,
        required=False,
    )
    if limit_fornecedores is _CANCELLED:
        return None
    ano_inicio = _prompt_int("Ano inicio (Enter para usar config)", default=None)
    if ano_inicio is _CANCELLED:
        return None
    ano_fim = _prompt_int("Ano fim exclusivo (Enter para usar config)", default=None)
    if ano_fim is _CANCELLED:
        return None

    tokens = ["extrair-portal-documentos"]
    if min_ocorrencias is not None:
        tokens.extend(["--min-ocorrencias", str(min_ocorrencias)])
    if limit_fornecedores is not None:
        tokens.extend(["--limit-fornecedores", str(limit_fornecedores)])
    if ano_inicio is not None:
        tokens.extend(["--ano-inicio", str(ano_inicio)])
    if ano_fim is not None:
        tokens.extend(["--ano-fim", str(ano_fim)])
    return tokens


def _build_obrasgov_geometrias() -> list[str] | None:
    """Monta os argumentos do extrator de geometrias do ObrasGov."""

    limit_ids = _prompt_int(
        "Limite de IDs (Enter para usar todos os IDs pendentes)",
        default=None,
        required=False,
    )
    if limit_ids is _CANCELLED:
        return None
    tokens = ["extrair-obrasgov-geometrias"]
    if limit_ids is not None:
        tokens.extend(["--limit-ids", str(limit_ids)])
    return tokens


def _build_anp() -> list[str] | None:
    """Monta os argumentos do extrator da ANP."""

    config = obter_parametros_cli("extrair_anp")
    min_ocorrencias = _prompt_int(
        "Minimo de ocorrencias",
        default=config.get("min_ocorrencias"),
        required=False,
    )
    if min_ocorrencias is _CANCELLED:
        return None
    if min_ocorrencias is None and config.get("min_ocorrencias") is None:
        return None

    limit_fornecedores = _prompt_int(
        "Limite de fornecedores (Enter para usar todos)",
        default=None,
        required=False,
    )
    if limit_fornecedores is _CANCELLED:
        return None

    tokens = ["extrair-anp"]
    if min_ocorrencias is not None:
        tokens.extend(["--min-ocorrencias", str(min_ocorrencias)])
    if limit_fornecedores is not None:
        tokens.extend(["--limit-fornecedores", str(limit_fornecedores)])
    return tokens


def build_menu_tree() -> tuple[MenuItem, ...]:
    """Cria a árvore de navegação do menu principal."""

    return (
        MenuItem(
            title="Pipelines",
            description="Executa os fluxos de maior nivel do projeto.",
            preview="rodar-pipeline | rodar-paralelo | rodar-pipeline-completo",
            tags=("pipeline", "orquestracao", "atalho"),
            icon="◆",
            accent="amber",
            children=(
                MenuItem(
                    title="Rodar pipeline da Camara",
                    description=(
                        "Executa legislaturas, deputados por legislatura, despesas "
                        "e consolidacao do CSV da Camara."
                    ),
                    preview="rodar-pipeline",
                    command_builder=_build_static("rodar-pipeline"),
                    tags=("camara", "pipeline", "csv"),
                    icon="▶",
                    accent="amber",
                ),
                MenuItem(
                    title="Rodar paralelo",
                    description=(
                        "Executa em paralelo as fontes independentes configuradas no projeto."
                    ),
                    preview="rodar-paralelo",
                    command_builder=_build_static("rodar-paralelo"),
                    tags=("paralelo", "fontes", "backbone"),
                    icon="∥",
                    accent="amber",
                ),
                MenuItem(
                    title="Rodar pipeline completo",
                    description=(
                        "Executa a extracao completa em fases, incluindo enriquecimentos."
                    ),
                    preview="rodar-pipeline-completo",
                    command_builder=_build_static("rodar-pipeline-completo"),
                    tags=("pipeline", "full-run", "etl"),
                    icon="★",
                    accent="amber",
                ),
                MenuItem(
                    title="Rodar pipeline do Portal",
                    description=(
                        "Executa dimensao de fornecedores, sancoes, notas e documentos."
                    ),
                    preview="rodar-pipeline-portal",
                    command_builder=_build_static("rodar-pipeline-portal"),
                    tags=("portal", "enriquecimento"),
                    icon="◈",
                    accent="amber",
                ),
            ),
        ),
        MenuItem(
            title="Olho Cidadão",
            description="Sobe a aplicacao publica em Loco.rs para explorar os dados em interface web.",
            preview="servir-cidadao-de-olho",
            tags=("web", "loco-rs", "publico"),
            icon="◉",
            accent="green",
            children=(
                MenuItem(
                    title="Abrir ambiente publico",
                    description=(
                        "Inicia o frontend e backend do Olho Cidadão sobre os artefatos locais do ETL."
                    ),
                    preview="servir-cidadao-de-olho",
                    command_builder=_build_static("servir-cidadao-de-olho"),
                    tags=("web", "frontend", "backend"),
                    icon="↗",
                    accent="green",
                ),
            ),
        ),
        MenuItem(
            title="Camara",
            description="Fluxos da Camara dos Deputados.",
            preview="baixar-legislaturas | extrair-legislaturas | extrair-dependentes",
            tags=("legislativo", "camara"),
            icon="◼",
            accent="blue",
            children=(
                MenuItem(
                    title="Baixar legislaturas",
                    description="Baixa a lista base de legislaturas da Camara.",
                    preview="baixar-legislaturas",
                    command_builder=_build_static("baixar-legislaturas"),
                    tags=("camara", "base", "legislaturas"),
                    icon="↓",
                    accent="blue",
                ),
                MenuItem(
                    title="Extrair legislaturas",
                    description="Extrai deputados vinculados a cada legislatura.",
                    preview="extrair-legislaturas",
                    command_builder=_build_static("extrair-legislaturas"),
                    tags=("camara", "deputados"),
                    icon="≣",
                    accent="blue",
                ),
                MenuItem(
                    title="Extrair dependentes",
                    description=(
                        "Extrai dados dependentes da Camara, como despesas dos deputados."
                    ),
                    preview="extrair-dependentes --endpoint deputados_despesas",
                    command_builder=_build_extrair_dependentes,
                    tags=("camara", "despesas", "parametrizado"),
                    interactive=True,
                    icon="¤",
                    accent="blue",
                ),
                MenuItem(
                    title="Gerar CSV",
                    description="Consolida o CSV final das despesas da Camara.",
                    preview="gerar-csv",
                    command_builder=_build_static("gerar-csv"),
                    tags=("csv", "consolidacao"),
                    icon="▤",
                    accent="blue",
                ),
            ),
        ),
        MenuItem(
            title="Portal da Transparencia",
            description="Enriquecimentos baseados na dimensao local de fornecedores.",
            preview="portal-construir-fornecedores | extrair-portal-*",
            tags=("portal", "fornecedores", "enriquecimento"),
            icon="⬢",
            accent="magenta",
            children=(
                MenuItem(
                    title="Construir dimensao de fornecedores",
                    description=(
                        "Reconstrui a dimensao local a partir dos dados de Camara e Senado."
                    ),
                    preview="portal-construir-fornecedores",
                    command_builder=_build_portal_fornecedores,
                    tags=("portal", "dimensao", "fornecedores"),
                    interactive=True,
                    icon="◎",
                    accent="magenta",
                ),
                MenuItem(
                    title="Extrair sancoes",
                    description="Consulta CEIS, CNEP e CEPIM para os fornecedores locais.",
                    preview="extrair-portal-sancoes",
                    command_builder=_build_portal_sancoes,
                    tags=("portal", "sancoes", "ceis", "cnep", "cepim"),
                    interactive=True,
                    icon="⚑",
                    accent="magenta",
                ),
                MenuItem(
                    title="Extrair notas fiscais",
                    description="Consulta notas fiscais do Portal da Transparencia.",
                    preview="extrair-portal-notas-fiscais",
                    command_builder=_build_portal_notas,
                    tags=("portal", "notas", "fiscal"),
                    interactive=True,
                    icon="✦",
                    accent="magenta",
                ),
                MenuItem(
                    title="Extrair documentos por favorecido",
                    description="Consulta documentos por favorecido no Portal.",
                    preview="extrair-portal-documentos",
                    command_builder=_build_portal_documentos,
                    tags=("portal", "documentos", "favorecido"),
                    interactive=True,
                    icon="☰",
                    accent="magenta",
                ),
            ),
        ),
        MenuItem(
            title="Fontes complementares",
            description="Extratores individuais de dados publicos e enriquecimento.",
            preview="senado | siop | ibge | pncp | transferegov | obrasgov | siconfi | anp",
            tags=("fontes", "publicas", "complementares"),
            icon="✳",
            accent="green",
            children=(
                MenuItem(
                    title="Extrair Senado",
                    description="Extrai dados do Senado Federal, como CEAPS.",
                    preview="extrair-senado",
                    command_builder=_build_static("extrair-senado"),
                    tags=("senado", "ceaps"),
                    icon="⌂",
                    accent="green",
                ),
                MenuItem(
                    title="Extrair SIOP",
                    description="Extrai dados orcamentarios do endpoint SPARQL do SIOP.",
                    preview="extrair-siop",
                    command_builder=_build_static("extrair-siop"),
                    tags=("siop", "orcamento", "sparql"),
                    icon="§",
                    accent="orange",
                ),
                MenuItem(
                    title="Extrair IBGE",
                    description="Extrai regioes, estados e municipios do IBGE.",
                    preview="extrair-ibge-localidades",
                    command_builder=_build_static("extrair-ibge-localidades"),
                    tags=("ibge", "territorio"),
                    icon="◉",
                    accent="cyan",
                ),
                MenuItem(
                    title="Extrair PNCP",
                    description="Extrai contratos, atas e PCA do PNCP.",
                    preview="extrair-pncp",
                    command_builder=_build_static("extrair-pncp"),
                    tags=("pncp", "contratos", "compras"),
                    icon="▣",
                    accent="teal",
                ),
                MenuItem(
                    title="Extrair Transferegov especial",
                    description="Extrai datasets do grupo Transferencias Especiais.",
                    preview="extrair-transferegov-especial",
                    command_builder=_build_static("extrair-transferegov-especial"),
                    tags=("transferegov", "especial"),
                    icon="⇄",
                    accent="lime",
                ),
                MenuItem(
                    title="Extrair Transferegov fundo a fundo",
                    description="Extrai datasets do grupo Fundo a Fundo.",
                    preview="extrair-transferegov-fundo",
                    command_builder=_build_static("extrair-transferegov-fundo"),
                    tags=("transferegov", "fundo-a-fundo"),
                    icon="⇆",
                    accent="lime",
                ),
                MenuItem(
                    title="Extrair Transferegov TED",
                    description="Extrai datasets do grupo TED.",
                    preview="extrair-transferegov-ted",
                    command_builder=_build_static("extrair-transferegov-ted"),
                    tags=("transferegov", "ted"),
                    icon="↔",
                    accent="lime",
                ),
                MenuItem(
                    title="Extrair ObrasGov",
                    description="Extrai projetos e execucoes do ObrasGov.",
                    preview="extrair-obrasgov",
                    command_builder=_build_static("extrair-obrasgov"),
                    tags=("obrasgov", "projetos", "execucao"),
                    icon="▥",
                    accent="yellow",
                ),
                MenuItem(
                    title="Extrair geometrias do ObrasGov",
                    description="Extrai geometrias para projetos ja persistidos.",
                    preview="extrair-obrasgov-geometrias",
                    command_builder=_build_obrasgov_geometrias,
                    tags=("obrasgov", "geometrias"),
                    interactive=True,
                    icon="⬡",
                    accent="yellow",
                ),
                MenuItem(
                    title="Extrair Siconfi",
                    description="Extrai o recurso padrao configurado do Siconfi.",
                    preview="extrair-siconfi",
                    command_builder=_build_static("extrair-siconfi"),
                    tags=("siconfi", "entes", "fiscal"),
                    icon="◫",
                    accent="violet",
                ),
                MenuItem(
                    title="Extrair ANP",
                    description="Extrai revendedores da ANP para os fornecedores locais.",
                    preview="extrair-anp",
                    command_builder=_build_anp,
                    tags=("anp", "combustivel", "glp"),
                    interactive=True,
                    icon="✺",
                    accent="pink",
                ),
            ),
        ),
    )


class TerminalMenu:
    """Renderiza e executa um menu interativo em terminal."""

    def __init__(self, items: tuple[MenuItem, ...]):
        self._items = items
        self._project_root = Path(__file__).resolve().parents[1]
        self._main_script = self._project_root / "main.py"
        self._alt_screen_active = False

    def run(self):
        """Inicia a navegacao do menu em modo TTY ou fallback numerico."""

        if sys.stdin.isatty() and sys.stdout.isatty():
            self._run_tty()
            return
        self._run_fallback()

    def _run_tty(self):
        state = MenuState()
        self._enter_alt_screen()
        try:
            while True:
                categorias = self._items
                categoria = categorias[state.category_index]
                itens = self._visible_items(categoria, state.query)
                state.item_index = self._clamp_item_index(
                    state.category_index,
                    itens,
                    state.item_index,
                    state,
                )

                self._render_dashboard(state, categoria, itens)
                key = self._read_key()

                if key in {"q", "Q"}:
                    return
                if key.isdigit() and key != "0":
                    self._jump_to_category(state, int(key) - 1)
                    continue
                if key in {"[", "]"}:
                    self._cycle_category(state, direction=-1 if key == "[" else 1)
                    continue
                if key == "\t":
                    state.focus = "categories" if state.focus == "items" else "items"
                    continue
                if key in {"h", "H", "LEFT"}:
                    state.focus = "categories"
                    continue
                if key in {"l", "L", "RIGHT"}:
                    state.focus = "items"
                    continue
                if key in {"b", "B"}:
                    state.focus = "categories"
                    continue
                if key in {"/"}:
                    query = self._prompt_search(state.query)
                    if query is not _CANCELLED:
                        state.query = query
                        state.item_index = 0
                        state.pending_prefix = ""
                    continue
                if key in {"c", "C"}:
                    state.query = ""
                    state.item_index = 0
                    state.pending_prefix = ""
                    continue
                if key in {"g"}:
                    state.item_index = 0
                    continue
                if key in {"G"} and itens:
                    state.item_index = len(itens) - 1
                    state.category_item_indices[state.category_index] = state.item_index
                    continue
                if key in {"PAGE_UP", "\x15"}:
                    self._move_page(state, itens, step=-5)
                    continue
                if key in {"PAGE_DOWN", "\x04"}:
                    self._move_page(state, itens, step=5)
                    continue
                if key in {"k", "K", "UP"}:
                    self._move_up(state, itens)
                    continue
                if key in {"j", "J", "DOWN"}:
                    self._move_down(state, itens)
                    continue
                if self._handle_item_shortcut(state, itens, key):
                    continue
                if key in {" ", "o", "O"}:
                    if itens:
                        self._execute_item(itens[state.item_index])
                    continue
                if key != "ENTER":
                    continue
                if state.focus == "categories":
                    state.focus = "items"
                    state.item_index = 0
                    continue
                if itens:
                    self._execute_item(itens[state.item_index])
        finally:
            self._leave_alt_screen()

    def _run_fallback(self):
        stack: list[tuple[str, tuple[MenuItem, ...]]] = [("Menu principal", self._items)]

        while stack:
            titulo, items = stack[-1]
            print(f"\n{titulo}")
            print("=" * len(titulo))
            for idx, item in enumerate(items, start=1):
                marcador = "/" if item.children else ""
                print(f"{idx}. {item.title}{marcador}")
            print("b. Voltar")
            print("q. Sair")

            escolha = input("Escolha uma opcao: ").strip().lower()
            if escolha == "q":
                return
            if escolha == "b":
                if len(stack) > 1:
                    stack.pop()
                continue
            if not escolha.isdigit():
                print("Opcao invalida.")
                continue

            indice = int(escolha) - 1
            if indice < 0 or indice >= len(items):
                print("Opcao invalida.")
                continue

            item = items[indice]
            if item.children:
                stack.append((item.title, item.children))
                continue
            self._execute_item(item)

    def _execute_item(self, item: MenuItem):
        tokens = item.command_builder() if item.command_builder else None
        if not tokens:
            self._wait_for_return("\nExecucao cancelada. Pressione Enter para voltar...")
            return

        if not (sys.stdin.isatty() and sys.stdout.isatty()):
            self._run_execution_fallback(tokens)
            return
        self._run_execution_console(item, tokens)

    def _render_dashboard(
        self,
        state: MenuState,
        categoria: MenuItem,
        itens: list[MenuItem],
    ):
        linhas: list[str] = []
        terminal_size = shutil.get_terminal_size((120, 34))
        largura = terminal_size.columns
        altura = terminal_size.lines
        total_comandos = sum(len(item.children) for item in self._items)
        selecionado = itens[state.item_index] if itens else None

        linhas.append(self._brand_bar(largura, total_comandos, state.query))
        linhas.append(self._breadcrumbs(categoria, selecionado))

        left_width = max(24, min(28, int(largura * 0.16)))
        center_width = max(44, min(72, int(largura * 0.30)))
        right_width = max(36, largura - left_width - center_width - 4)

        esquerda = self._panel(
            "Seções",
            self._build_categories_lines(state),
            width=left_width,
        )
        centro = self._panel(
            categoria.title,
            self._build_items_lines(itens, state),
            width=center_width,
        )
        direita = self._panel(
            "Inspector",
            self._build_details_lines(categoria, selecionado, state),
            width=right_width,
        )

        for line in self._merge_columns(esquerda, centro, direita):
            linhas.append(line)

        atividade = self._panel(
            "Activity feed",
            self._build_activity_lines(limit=max(8, min(12, altura // 3))),
            width=max(60, largura - 2),
        )
        for line in atividade:
            linhas.append(line)

        linhas.append(self._footer_bar())
        self._render_screen(linhas)

    def _build_categories_lines(self, state: MenuState) -> list[str]:
        linhas = [
            f"{_MUTED}1-9 pula secoes | [ ] alterna | h/l muda foco{_RESET}",
            "",
        ]
        for idx, item in enumerate(self._items):
            badge = f"{len(item.children):02d}"
            atalhos = f"{idx + 1}"
            cor_item = self._accent_color(item.accent)
            plain = f"{atalhos}. {item.icon} {item.title}"
            extra = f"{badge} cmd"
            texto = self._truncate(plain, 14)
            if idx == state.category_index:
                linhas.append(
                    f"{cor_item}▌{_RESET} {cor_item}{texto:<14}{_RESET} "
                    f"{self._tag(extra, tone=item.accent)}"
                )
            else:
                linhas.append(
                    f"  {cor_item}{texto:<14}{_RESET} {self._tag(extra, tone='muted')}"
                )
        return linhas

    def _build_items_lines(self, itens: list[MenuItem], state: MenuState) -> list[str]:
        if not itens:
            return [
                "",
                f"{_RED}Nenhum comando encontrado para a busca atual.{_RESET}",
                f"{_MUTED}Pressione c para limpar o filtro.{_RESET}",
            ]

        linhas = [
            f"{_MUTED}Enter ou espaco executa | / busca | Ctrl-D/U pagina | letras pulam{_RESET}",
            "",
        ]
        for idx, item in enumerate(itens):
            atalho = self._item_shortcut(idx)
            marker = "▸" if idx == state.item_index else " "
            cor_item = self._accent_color(item.accent)
            prefixo = f"{atalho} " if atalho else ""
            titulo = self._truncate(prefixo + item.icon + " " + item.title, 34)
            preview = self._truncate(item.preview, 38)
            if idx == state.item_index:
                linhas.append(f"{cor_item}{marker} {titulo}{_RESET}")
                linhas.append(
                    f"  {self._tag('prompt' if item.interactive else 'direto', tone=item.accent)} "
                    f"{self._tag(atalho.upper() if atalho else '•', tone='muted')} {preview}"
                )
                linhas.append(f"  {_SOFT}{self._truncate(item.description, 46)}{_RESET}")
            else:
                linhas.append(f"{cor_item}{marker} {titulo}{_RESET}")
                linhas.append(f"  {self._truncate(preview, 46)}")
            linhas.append("")
        return linhas

    def _build_details_lines(
        self,
        categoria: MenuItem,
        selecionado: MenuItem | None,
        state: MenuState,
    ) -> list[str]:
        if selecionado is None:
            return [
                "",
                "Nenhum comando visivel nesta secao.",
                "",
                "Use / para procurar por titulo ou descricao.",
            ]

        linhas = [
            f"{self._accent_color(selecionado.accent)}{_BOLD}{selecionado.icon} {selecionado.title}{_RESET}",
            f"{_SOFT}{selecionado.description}{_RESET}",
            "",
            (
                f"{_MUTED}Categoria:{_RESET} "
                f"{self._accent_color(categoria.accent)}{categoria.icon} {categoria.title}{_RESET}"
            ),
            (
                f"{_MUTED}Modo:{_RESET} "
                f"{_PINK}Com prompts{_RESET}"
                if selecionado.interactive
                else f"{_MUTED}Modo:{_RESET} {_GREEN}Execucao direta{_RESET}"
            ),
            f"{_MUTED}Comando:{_RESET} {self._accent_color(selecionado.accent)}{selecionado.preview}{_RESET}",
            f"{_MUTED}Tags:{_RESET} " + " ".join(self._tag(tag) for tag in (selecionado.tags or ("etl",))),
            f"{_MUTED}Busca:{_RESET} {state.query or 'sem filtro'}",
            "",
            f"{_MUTED}Atalhos:{_RESET} 1-9 secoes | a-z comandos | Enter/espaco executa",
            f"{_MUTED}Navegacao:{_RESET} j/k ou setas | Ctrl-D/U pagina | [ ] troca secao | / busca",
        ]
        return linhas

    def _brand_bar(self, largura: int, total_comandos: int, query: str) -> str:
        faixa = min(largura, 120)
        titulo = (
            f"{_BOLD}{_AMBER}br{_RESET}"
            f"{_BOLD}{_BLUE}_ETL{_RESET} "
            f"{_BOLD}{_MAGENTA}COMMAND{_RESET} "
            f"{_BOLD}{_GREEN}CENTER{_RESET}"
        )
        subtitulo = (
            f"{_DIM}TUI orientado a teclado para explorar "
            f"{_CYAN}pipelines{_RESET}{_DIM} e { _YELLOW}extratores{_RESET}{_DIM}{_RESET}"
        )
        badges = " ".join(
            [
                self._tag(f"{len(self._items)} secoes", tone="amber"),
                self._tag(f"{total_comandos} comandos", tone="blue"),
                self._tag("etl-config.toml", tone="magenta"),
                self._tag(f"filtro: {query}" if query else "sem filtro", tone="green"),
            ]
        )
        return "\n".join(
            [
                titulo,
                subtitulo,
                badges,
                f"{_SLATE}{'═' * faixa}{_RESET}",
            ]
        )

    def _footer_bar(self) -> str:
        return (
            f"{_SLATE}{'═' * 100}{_RESET}\n"
            f"{_DIM}1-9 secoes | a-z comandos | Enter/espaco executa | "
            f"[ ] alterna secao | / busca | c limpa | q sai{_RESET}"
        )

    def _build_activity_lines(self, *, limit: int) -> list[str]:
        linhas = self._tail_log_lines(limit=limit)
        if not linhas:
            return [
                f"{_MUTED}Nenhuma atividade recente no log principal.{_RESET}",
                f"{_MUTED}As execucoes disparadas pelo menu aparecem aqui.{_RESET}",
            ]
        return [self._colorize_log_line(self._truncate(line, 112)) for line in linhas]

    def _visible_items(self, categoria: MenuItem, query: str) -> list[MenuItem]:
        if not query:
            return list(categoria.children)
        termo = query.casefold()
        return [
            item
            for item in categoria.children
            if termo in item.title.casefold()
            or termo in item.description.casefold()
            or termo in item.preview.casefold()
            or any(termo in tag.casefold() for tag in item.tags)
        ]

    def _move_up(self, state: MenuState, itens: list[MenuItem]):
        if state.focus == "categories":
            state.category_index = (state.category_index - 1) % len(self._items)
            state.item_index = state.category_item_indices.get(state.category_index, 0)
            return
        if itens:
            state.item_index = (state.item_index - 1) % len(itens)
            state.category_item_indices[state.category_index] = state.item_index

    def _move_down(self, state: MenuState, itens: list[MenuItem]):
        if state.focus == "categories":
            state.category_index = (state.category_index + 1) % len(self._items)
            state.item_index = state.category_item_indices.get(state.category_index, 0)
            return
        if itens:
            state.item_index = (state.item_index + 1) % len(itens)
            state.category_item_indices[state.category_index] = state.item_index

    def _move_page(self, state: MenuState, itens: list[MenuItem], *, step: int):
        if state.focus == "categories":
            self._cycle_category(state, direction=step)
            return
        if itens:
            state.item_index = max(0, min(len(itens) - 1, state.item_index + step))
            state.category_item_indices[state.category_index] = state.item_index

    def _cycle_category(self, state: MenuState, *, direction: int):
        total = len(self._items)
        state.category_index = (state.category_index + direction) % total
        state.item_index = state.category_item_indices.get(state.category_index, 0)

    def _jump_to_category(self, state: MenuState, index: int):
        if 0 <= index < len(self._items):
            state.category_index = index
            state.item_index = state.category_item_indices.get(index, 0)
            state.focus = "items"

    def _clamp_item_index(
        self,
        category_index: int,
        itens: list[MenuItem],
        current_index: int,
        state: MenuState,
    ) -> int:
        if not itens:
            state.category_item_indices[category_index] = 0
            return 0
        remembered = state.category_item_indices.get(category_index, current_index)
        clamped = max(0, min(remembered, len(itens) - 1))
        state.category_item_indices[category_index] = clamped
        return clamped

    def _item_shortcut(self, index: int) -> str:
        if 0 <= index < 26:
            return chr(ord("a") + index)
        return ""

    def _handle_item_shortcut(self, state: MenuState, itens: list[MenuItem], key: str) -> bool:
        if not itens or not key.isalpha() or len(key) != 1:
            state.pending_prefix = ""
            return False
        idx = ord(key.lower()) - ord("a")
        if idx < 0 or idx >= len(itens):
            return False
        state.item_index = idx
        state.category_item_indices[state.category_index] = idx
        state.focus = "items"
        return True

    def _breadcrumbs(self, categoria: MenuItem, selecionado: MenuItem | None) -> str:
        partes = [
            self._tag("menu", tone="amber"),
            self._tag(f"{categoria.icon} {categoria.title}", tone=categoria.accent),
        ]
        if selecionado is not None:
            partes.append(
                self._tag(f"{selecionado.icon} {selecionado.title}", tone=selecionado.accent)
            )
        return " ".join(partes)

    def _tail_log_lines(self, *, limit: int) -> list[str]:
        path = Path(LOG_FILE)
        if not path.exists():
            return []
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                return [line.rstrip() for line in deque(f, maxlen=limit)]
        except OSError:
            return []

    def _colorize_log_line(self, line: str) -> str:
        if " - ERROR - " in line or " | ERROR | " in line:
            return f"{_RED}{line}{_RESET}"
        if " - WARNING - " in line or " | WARNING | " in line:
            return f"{_ORANGE}{line}{_RESET}"
        if " - INFO - " in line or " | INFO | " in line:
            return f"{_CYAN}{line}{_RESET}"
        return f"{_MUTED}{line}{_RESET}"

    def _run_execution_console(self, item: MenuItem, tokens: list[str]):
        sink: deque[str] = deque(maxlen=200)
        result = ExecutionResult()
        command = self._build_cli_command(tokens)
        display_command = self._build_display_command(tokens)
        started_at = time.monotonic()
        sink.append(f"Iniciando comando: {display_command}")

        processo = subprocess.Popen(
            command,
            cwd=self._project_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        readers = [
            threading.Thread(
                target=self._pipe_reader,
                args=(processo.stdout, sink, None),
                daemon=True,
            ),
            threading.Thread(
                target=self._pipe_reader,
                args=(processo.stderr, sink, "stderr"),
                daemon=True,
            ),
        ]
        for reader in readers:
            reader.start()

        frame = 0
        while True:
            exit_code = processo.poll()
            running = exit_code is None
            status = "running" if running else self._status_from_exit_code(exit_code)
            result.status = status
            result.exit_code = exit_code
            self._render_execution_screen(
                item,
                display_command,
                sink,
                frame,
                status=status,
                elapsed=time.monotonic() - started_at,
            )
            frame += 1

            key = self._read_key_nonblocking(timeout=0.08 if running else 0.2)
            if running and key in {"x", "X", "\x03"}:
                sink.append("Solicitando interrupcao do comando...")
                processo.terminate()
                continue
            if not running:
                break

        for reader in readers:
            reader.join(timeout=0.5)

        if result.exit_code not in (0, None) and not sink:
            sink.append(f"Comando finalizado com codigo {result.exit_code}.")

        self._render_execution_screen(
            item,
            display_command,
            sink,
            frame,
            status=result.status,
            elapsed=time.monotonic() - started_at,
        )
        self._wait_for_return("")

    def _render_execution_screen(
        self,
        item: MenuItem,
        display_command: str,
        sink: deque[str],
        frame: int,
        *,
        status: str,
        elapsed: float,
    ):
        linhas: list[str] = []
        spinner = _SPINNER[frame % len(_SPINNER)]
        status_chip = {
            "running": self._tag(f"{spinner} executando", tone="cyan"),
            "success": self._tag("sucesso", tone="green"),
            "error": self._tag("falha", tone="red"),
            "cancelled": self._tag("interrompido", tone="orange"),
        }.get(status, self._tag(status))

        linhas.append(
            f"{_BOLD}{_AMBER}br{_RESET}{_BOLD}{_BLUE}_ETL{_RESET} "
            f"{_BOLD}{_MAGENTA}RUN{_RESET} {status_chip}"
        )
        linhas.append(f"{self._accent_color(item.accent)}{item.icon} {item.title}{_RESET}")
        linhas.append(f"{_SOFT}{item.description}{_RESET}")
        linhas.append(f"{_SLATE}{'═' * 110}{_RESET}")

        resumo = self._panel(
            "Resumo da execucao",
            [
                f"{_MUTED}Comando{_RESET}",
                f"{self._accent_color(item.accent)}{display_command}{_RESET}",
                "",
                f"{_MUTED}Modo{_RESET}",
                (
                    f"{_PINK}Com prompts{_RESET}"
                    if item.interactive
                    else f"{_GREEN}Execucao direta{_RESET}"
                ),
                "",
                f"{_MUTED}Status{_RESET}",
                status_chip,
                "",
                f"{_MUTED}Tempo decorrido{_RESET}",
                self._format_elapsed(elapsed),
            ],
            width=40,
        )
        activity = self._panel(
            "Mensagens ao vivo",
            self._build_execution_log_lines(sink),
            width=68,
        )
        for line in self._merge_columns(resumo, activity):
            linhas.append(line)

        linhas.append(
            f"{_SLATE}{'═' * 110}{_RESET}\n"
            f"{_DIM}x interrompe | Enter volta apos concluir | logs e saida do comando aparecem aqui.{_RESET}"
        )
        self._render_screen(linhas)

    def _build_execution_log_lines(self, sink: deque[str]) -> list[str]:
        if not sink:
            return [f"{_MUTED}Aguardando mensagens...{_RESET}"]
        return [self._colorize_log_line(self._truncate(line, 66)) for line in list(sink)[-16:]]

    def _run_execution_fallback(self, tokens: list[str]):
        subprocess.run(
            self._build_cli_command(tokens),
            cwd=self._project_root,
            check=False,
        )
        input("\nPressione Enter para voltar ao menu...")

    def _pipe_reader(
        self,
        pipe,
        sink: deque[str],
        source: str | None,
    ):
        if pipe is None:
            return
        try:
            for raw_line in iter(pipe.readline, ""):
                line = raw_line.rstrip()
                if not line:
                    continue
                prefix = f"[{source}] " if source else ""
                sink.append(prefix + line)
        finally:
            pipe.close()

    def _build_cli_command(self, tokens: list[str]) -> list[str]:
        return [sys.executable, str(self._main_script), *tokens]

    def _build_display_command(self, tokens: list[str]) -> str:
        return f"{Path(sys.executable).name} main.py {' '.join(tokens)}"

    def _status_from_exit_code(self, exit_code: int | None) -> str:
        if exit_code in (None, 0):
            return "success"
        if exit_code == -15:
            return "cancelled"
        return "error"

    def _format_elapsed(self, elapsed: float) -> str:
        total = max(0, int(elapsed))
        minutos, segundos = divmod(total, 60)
        horas, minutos = divmod(minutos, 60)
        if horas:
            return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        return f"{minutos:02d}:{segundos:02d}"

    def _wait_for_return(self, prefix: str):
        if prefix:
            print(prefix, flush=True)
        while True:
            key = self._read_key()
            if key in {"ENTER", "q", "Q", " "}:
                return

    def _prompt_search(self, atual: str) -> str | object:
        self._render_screen(
            [
                f"{_BOLD}{_AMBER}Filtro de comandos{_RESET}",
                f"{_MUTED}Filtra por titulo, descricao, preview ou tag. q cancela.{_RESET}",
                "",
            ]
        )
        valor = input(f"Busca [{atual}]: ").strip()
        if valor.lower() == "q":
            return _CANCELLED
        return valor

    def _panel(self, title: str, lines: list[str], width: int) -> list[str]:
        inner = max(12, width - 2)
        saida = [f"{_PANEL}┌{'─' * inner}┐{_RESET}"]
        cabecalho = self._truncate(title, inner - 1)
        saida.append(f"{_PANEL}│{_RESET}{_BOLD} {cabecalho:<{inner - 1}}{_RESET}{_PANEL}│{_RESET}")
        saida.append(f"{_PANEL}├{'─' * inner}┤{_RESET}")
        for raw in lines:
            blocos = self._wrap_line(raw, inner)
            if not blocos:
                blocos = [""]
            for bloco in blocos:
                plain_len = len(self._strip_ansi(bloco))
                padding = " " * max(0, inner - plain_len)
                saida.append(f"{_PANEL}│{_RESET}{bloco}{padding}{_PANEL}│{_RESET}")
        saida.append(f"{_PANEL}└{'─' * inner}┘{_RESET}")
        return saida

    def _merge_columns(self, *columns: list[str]) -> list[str]:
        altura = max(len(col) for col in columns)
        widths = [max(len(self._strip_ansi(line)) for line in col) for col in columns]
        linhas: list[str] = []
        for idx in range(altura):
            partes = []
            for col, width in zip(columns, widths, strict=True):
                valor = col[idx] if idx < len(col) else " " * width
                pad = " " * max(0, width - len(self._strip_ansi(valor)))
                partes.append(valor + pad)
            linhas.append("  ".join(partes))
        return linhas

    def _wrap_line(self, text: str, width: int) -> list[str]:
        if not text:
            return [""]
        if "\033[" in text:
            return [self._truncate(text, width)]
        return textwrap.wrap(text, width=width, break_long_words=False) or [""]

    def _truncate(self, text: str, width: int) -> str:
        plain = self._strip_ansi(text)
        if len(plain) <= width:
            return text
        return textwrap.shorten(plain, width=width, placeholder="…")

    def _tag(self, text: str, tone: str = "default") -> str:
        cor = {
            "default": _BLUE,
            "accent": _AMBER,
            "amber": _AMBER,
            "blue": _BLUE,
            "green": _GREEN,
            "cyan": _CYAN,
            "teal": _TEAL,
            "magenta": _MAGENTA,
            "violet": _VIOLET,
            "pink": _PINK,
            "yellow": _YELLOW,
            "lime": _LIME,
            "orange": _ORANGE,
            "red": _RED,
            "muted": _MUTED,
        }.get(tone, _BLUE)
        return f"{cor}[{text}]{_RESET}"

    def _accent_color(self, tone: str) -> str:
        return {
            "default": _BLUE,
            "amber": _AMBER,
            "blue": _BLUE,
            "green": _GREEN,
            "cyan": _CYAN,
            "teal": _TEAL,
            "magenta": _MAGENTA,
            "violet": _VIOLET,
            "pink": _PINK,
            "yellow": _YELLOW,
            "lime": _LIME,
            "orange": _ORANGE,
        }.get(tone, _BLUE)

    def _strip_ansi(self, text: str) -> str:
        resultado = []
        skip = False
        for ch in text:
            if ch == "\033":
                skip = True
                continue
            if skip:
                if ch == "m":
                    skip = False
                continue
            resultado.append(ch)
        return "".join(resultado)

    def _read_key(self) -> str:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            first = sys.stdin.read(1)
            if first == "\x1b":
                second = sys.stdin.read(1)
                if second == "[":
                    third = sys.stdin.read(1)
                    if third in {"5", "6"}:
                        sys.stdin.read(1)
                        return {"5": "PAGE_UP", "6": "PAGE_DOWN"}[third]
                    return {
                        "A": "UP",
                        "B": "DOWN",
                        "C": "RIGHT",
                        "D": "LEFT",
                    }.get(third, "ESC")
            if first in {"\r", "\n"}:
                return "ENTER"
            if first == "\x03":
                return "\x03"
            if first == "\x7f":
                return "BACKSPACE"
            return first
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _read_key_nonblocking(self, *, timeout: float) -> str | None:
        if not sys.stdin.isatty():
            time.sleep(timeout)
            return None
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if not ready:
            return None
        return self._read_key()

    def _render_screen(self, lines: list[str]):
        quadro = "\n".join(lines)
        if self._alt_screen_active:
            sys.stdout.write(_HOME + _CLEAR + quadro)
            sys.stdout.flush()
            return
        print(_CLEAR + quadro, end="", flush=True)

    def _enter_alt_screen(self):
        if self._alt_screen_active:
            return
        sys.stdout.write(_ALT_SCREEN_ON + _HIDE_CURSOR + _CLEAR)
        sys.stdout.flush()
        self._alt_screen_active = True

    def _leave_alt_screen(self):
        if not self._alt_screen_active:
            return
        sys.stdout.write(_SHOW_CURSOR + _ALT_SCREEN_OFF)
        sys.stdout.flush()
        self._alt_screen_active = False

    def _clear(self):
        self._render_screen([])


def open_terminal_menu():
    """Abre o menu interativo do projeto."""

    TerminalMenu(build_menu_tree()).run()
