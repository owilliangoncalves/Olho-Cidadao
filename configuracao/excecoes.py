class ConfiguracaoErro(Exception):
    """Erro base de configuração."""


class ArquivoConfiguracaoNaoEncontrado(ConfiguracaoErro):
    """Arquivo de configuração ausente."""


class ConfiguracaoInvalida(ConfiguracaoErro):
    """Estrutura ou valores inválidos no arquivo de configuração."""


class ChaveConfiguracaoNaoEncontrada(ConfiguracaoErro):
    """Caminho solicitado não existe na configuração."""