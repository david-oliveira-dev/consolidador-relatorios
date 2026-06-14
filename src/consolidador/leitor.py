"""Leitura dos arquivos de uma pasta.

Responsabilidade única desta fase: *encontrar* e *ler* os arquivos, sem
limpar nem transformar nada ainda. Cada aba lida vira um objeto `Planilha`
que carrega o DataFrame e a sua origem (arquivo + aba), para rastreabilidade.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Extensões que sabemos ler. Mantido como constante para facilitar manutenção.
EXTENSOES_EXCEL = {".xlsx", ".xls"}
EXTENSOES_CSV = {".csv"}
EXTENSOES_SUPORTADAS = EXTENSOES_EXCEL | EXTENSOES_CSV


class ErroLeitura(Exception):
    """Erro de leitura com mensagem amigável (em português) para o usuário final."""


@dataclass
class Planilha:
    """Uma tabela lida de um arquivo, com sua origem registrada.

    Attributes:
        df: os dados crus, exatamente como vieram do arquivo (sem limpeza).
        arquivo: nome do arquivo de origem (ex.: 'vendas_janeiro.xlsx').
        aba: nome da aba (para Excel) ou None (para CSV).
    """

    df: pd.DataFrame
    arquivo: str
    aba: str | None = None

    @property
    def origem(self) -> str:
        """Texto legível da origem, ex.: 'vendas_abril.xlsx[Vendas]'."""
        return f"{self.arquivo}[{self.aba}]" if self.aba else self.arquivo


def encontrar_arquivos(pasta: Path) -> list[Path]:
    """Lista os arquivos suportados dentro de `pasta` (ordenados por nome).

    Ignora arquivos auxiliares (ex.: '_gerar_dados.py') e qualquer extensão
    que não saibamos ler. Levanta ErroLeitura se a pasta não existir.
    """
    if not pasta.exists():
        raise ErroLeitura(f"A pasta '{pasta}' não existe. Verifique o caminho informado.")
    if not pasta.is_dir():
        raise ErroLeitura(f"'{pasta}' não é uma pasta.")

    arquivos = [
        caminho
        for caminho in sorted(pasta.iterdir())
        if caminho.is_file() and caminho.suffix.lower() in EXTENSOES_SUPORTADAS
    ]
    return arquivos


def _ler_csv(caminho: Path) -> list[Planilha]:
    """Lê um CSV detectando o separador automaticamente (',' ou ';').

    sep=None + engine='python' faz o pandas "farejar" o separador, resolvendo
    o caso brasileiro do ';' sem precisar configurar nada à mão.
    """
    df = pd.read_csv(caminho, sep=None, engine="python", dtype=str)
    return [Planilha(df=df, arquivo=caminho.name, aba=None)]


def _ler_excel(caminho: Path) -> list[Planilha]:
    """Lê TODAS as abas de um Excel. sheet_name=None devolve {aba: DataFrame}."""
    try:
        # dtype=str: lemos tudo como texto nesta fase para não perder a formatação
        # original (ex.: "1.200,50"). A conversão de tipos acontece na limpeza.
        abas = pd.read_excel(caminho, sheet_name=None, dtype=str)
    except ImportError as exc:
        # .xls (formato antigo) precisa da biblioteca 'xlrd', que não instalamos.
        raise ErroLeitura(
            f"Não foi possível ler '{caminho.name}'. Arquivos .xls antigos "
            "exigem a biblioteca 'xlrd'. Salve como .xlsx ou instale xlrd."
        ) from exc

    return [Planilha(df=df, arquivo=caminho.name, aba=nome_aba) for nome_aba, df in abas.items()]


def ler_pasta(pasta: Path) -> list[Planilha]:
    """Lê todos os arquivos suportados de uma pasta e devolve uma lista de Planilha.

    Cada aba de cada Excel vira uma Planilha separada; cada CSV vira uma.
    Levanta ErroLeitura se a pasta estiver vazia (sem arquivos suportados) ou
    se algum arquivo estiver corrompido/ilegível — sempre com mensagem clara.
    """
    arquivos = encontrar_arquivos(pasta)
    if not arquivos:
        raise ErroLeitura(
            f"Nenhum arquivo .xlsx, .xls ou .csv encontrado em '{pasta}'. "
            "Coloque suas planilhas nessa pasta e tente de novo."
        )

    planilhas: list[Planilha] = []
    for caminho in arquivos:
        try:
            if caminho.suffix.lower() in EXTENSOES_CSV:
                planilhas.extend(_ler_csv(caminho))
            else:
                planilhas.extend(_ler_excel(caminho))
        except ErroLeitura:
            raise  # já é amigável, repassa
        except Exception as exc:  # noqa: BLE001 — vira mensagem amigável
            raise ErroLeitura(
                f"Não foi possível ler '{caminho.name}'. O arquivo pode estar "
                f"corrompido ou em formato inesperado. Detalhe técnico: {exc}"
            ) from exc

    return planilhas
