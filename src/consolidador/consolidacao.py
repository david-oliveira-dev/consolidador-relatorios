"""Consolidação: junta todas as planilhas limpas num único DataFrame.

Recebe a lista de `Planilha` (crua) do leitor, limpa cada uma (Fase 3),
descarta o que não parece dado de venda (ex.: aba 'Rascunho'), carimba a
origem e empilha tudo com pd.concat — que alinha colunas automaticamente.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from consolidador.leitor import Planilha
from consolidador.limpeza import limpar_dataframe

# Para uma planilha ser considerada "de vendas", precisa ter pelo menos estas
# colunas canônicas. A aba 'Rascunho' (só 'obs') é descartada por este filtro.
COLUNAS_ESSENCIAIS = {"produto", "valor"}

# Ordem preferida das colunas no resultado final (as demais vão para o fim).
ORDEM_PREFERIDA = ["data", "produto", "quantidade", "valor", "regiao", "origem"]


class ErroConsolidacao(Exception):
    """Erro de consolidação com mensagem amigável em português."""


@dataclass
class ResultadoConsolidacao:
    """Resultado da consolidação: os dados e o relato do que foi descartado."""

    dados: pd.DataFrame
    descartadas: list[str] = field(default_factory=list)  # origens ignoradas


def _ordenar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Coloca as colunas conhecidas numa ordem amigável; o resto vai ao final."""
    conhecidas = [c for c in ORDEM_PREFERIDA if c in df.columns]
    extras = [c for c in df.columns if c not in ORDEM_PREFERIDA]
    return df[conhecidas + extras]


def consolidar(
    planilhas: list[Planilha],
    mapeamento: dict[str, str] | None = None,
    colunas_essenciais: set[str] = COLUNAS_ESSENCIAIS,
) -> ResultadoConsolidacao:
    """Limpa, filtra e junta todas as planilhas num DataFrame único.

    Args:
        planilhas: saída do leitor (DataFrames crus + origem).
        mapeamento: mapeamento canônico de colunas (opcional; usa o padrão).
        colunas_essenciais: colunas mínimas para a planilha contar como venda.

    Returns:
        ResultadoConsolidacao com os dados consolidados e as origens descartadas.

    Raises:
        ErroConsolidacao: se nenhuma planilha tiver os dados mínimos de venda.
    """
    frames: list[pd.DataFrame] = []
    descartadas: list[str] = []

    for planilha in planilhas:
        limpo = limpar_dataframe(planilha.df, mapeamento)

        # Sem as colunas essenciais, não é dado de venda -> descarta (ex.: Rascunho).
        if not colunas_essenciais.issubset(limpo.columns):
            descartadas.append(planilha.origem)
            continue

        # Carimba a origem para rastreabilidade no relatório final.
        limpo = limpo.copy()
        limpo["origem"] = planilha.origem
        frames.append(limpo)

    if not frames:
        raise ErroConsolidacao(
            "Nenhuma planilha com dados de venda foi encontrada. Verifique se os "
            f"arquivos têm pelo menos as colunas: {', '.join(sorted(colunas_essenciais))}."
        )

    # concat alinha colunas pelo nome: quem não tem 'regiao' recebe NaN ali.
    consolidado = pd.concat(frames, ignore_index=True)
    consolidado = _ordenar_colunas(consolidado)
    return ResultadoConsolidacao(dados=consolidado, descartadas=descartadas)
