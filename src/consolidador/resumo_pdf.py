"""PDF executivo de 1 página — o "print bonito" do portfólio.

Mostra os números-chave (KPIs) e um gráfico de faturamento por produto.

Decisão de design: gerado 100% com matplotlib. Para uma página única, isso dá
saída vetorial (nítida em qualquer zoom) com uma só ferramenta, sem precisar
criar imagem temporária e montar layout à parte. As métricas reaproveitam as
funções de resumo já testadas em `relatorio.py`.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sem janela (geramos arquivo, não exibimos)
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from consolidador.relatorio import resumo_por_produto  # noqa: E402

_AZUL = "#305496"
_CINZA = "#595959"


def formatar_brl(valor: float) -> str:
    """Formata número no padrão monetário brasileiro: 1234.5 -> 'R$ 1.234,50'.

    O Python formata no estilo americano (1,234.50); trocamos os separadores
    via um marcador temporário para chegar no estilo brasileiro.
    """
    texto = f"{valor:,.2f}"  # '1,234.50'
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def calcular_kpis(df: pd.DataFrame) -> dict[str, str]:
    """Calcula os 4 números-chave exibidos no topo do PDF."""
    faturamento_total = df["valor"].sum()
    num_vendas = int(df["valor"].count())
    ticket_medio = df["valor"].mean()
    campeao = resumo_por_produto(df).iloc[0]["produto"]  # já vem ordenado desc
    return {
        "Faturamento total": formatar_brl(faturamento_total),
        "Nº de vendas": f"{num_vendas}",
        "Ticket médio": formatar_brl(ticket_medio),
        "Produto campeão": str(campeao),
    }


def _desenhar_cartao(fig, x: float, titulo: str, valor: str) -> None:
    """Desenha um 'cartão' de KPI (rótulo pequeno + número grande) na figura."""
    fig.text(x, 0.86, titulo, ha="center", fontsize=11, color=_CINZA)
    fig.text(x, 0.81, valor, ha="center", fontsize=17, fontweight="bold", color=_AZUL)


def gerar_resumo_pdf(df: pd.DataFrame, caminho_saida: Path) -> Path:
    """Gera o PDF executivo de 1 página em `caminho_saida` e retorna o caminho."""
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    kpis = calcular_kpis(df)
    rp = resumo_por_produto(df)

    # Página A4 retrato (em polegadas).
    fig = plt.figure(figsize=(8.27, 11.69))

    # --- Título ---
    fig.text(0.5, 0.95, "Relatório Consolidado de Vendas", ha="center",
             fontsize=22, fontweight="bold", color=_AZUL)
    fig.text(0.5, 0.915, "Resumo executivo", ha="center", fontsize=12, color=_CINZA)

    # --- 4 cartões de KPI distribuídos na horizontal ---
    posicoes_x = [0.16, 0.38, 0.62, 0.85]
    for x, (titulo, valor) in zip(posicoes_x, kpis.items()):
        _desenhar_cartao(fig, x, titulo, valor)

    # --- Gráfico de barras: faturamento por produto ---
    ax = fig.add_axes((0.12, 0.10, 0.78, 0.58))  # [esq, base, larg, alt]
    barras = ax.bar(rp["produto"], rp["faturamento"], color=_AZUL)
    ax.set_title("Faturamento por Produto", fontsize=14, pad=12)
    ax.set_ylabel("R$")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="x", rotation=20)

    # rótulo do valor em cima de cada barra
    for barra, valor in zip(barras, rp["faturamento"]):
        ax.text(barra.get_x() + barra.get_width() / 2, valor,
                formatar_brl(valor), ha="center", va="bottom", fontsize=8)
    ax.margins(y=0.15)  # espaço pro rótulo não encostar no topo

    # --- Rodapé ---
    fontes = df["origem"].nunique()
    fig.text(0.5, 0.04,
             f"Gerado automaticamente pelo Consolidador de Relatórios • "
             f"{len(df)} registros de {fontes} fontes",
             ha="center", fontsize=9, color=_CINZA)

    fig.savefig(caminho_saida, format="pdf")
    plt.close(fig)  # libera memória (importante ao gerar vários relatórios)
    return caminho_saida
