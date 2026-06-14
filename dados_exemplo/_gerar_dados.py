"""Gera planilhas de exemplo PROPOSITALMENTE bagunçadas.

A graça do projeto é transformar dados sujos em um relatório limpo. Para
demonstrar isso sem usar dado real de cliente, este script cria arquivos
sintéticos com os problemas típicos do mundo real:

  - nomes de coluna inconsistentes ("Data da Venda", "DT", "data", "Data")
  - números em formatos diferentes (BR "1.200,50" como texto x US 1200.5 float)
  - nomes de produto com espaços extras e maiúsculas/minúsculas variando
  - células vazias e linhas totalmente em branco
  - CSV com separador ";" (padrão comum no Brasil)
  - um arquivo com uma aba extra de "Rascunho" (lixo) além da aba de dados

Rode com:  python dados_exemplo/_gerar_dados.py
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# Semente fixa => os mesmos arquivos toda vez (reprodutível para o portfólio).
random.seed(42)

PASTA = Path(__file__).parent

PRODUTOS = ["Café 500g", "Açúcar 1kg", "Farinha de Trigo", "Arroz 5kg", "Feijão 1kg"]
VENDEDORES = ["Ana", "Bruno", "Carla", "Diego"]


def _valor_br(valor: float) -> str:
    """Formata um número no padrão brasileiro como TEXTO: 1234.5 -> '1.234,50'.

    Retornar string é de propósito: simula a planilha onde o valor foi digitado
    como texto, um dos problemas que a fase de limpeza terá de resolver.
    """
    inteiro, centavos = f"{valor:,.2f}".split(".")
    inteiro = inteiro.replace(",", ".")  # separador de milhar vira ponto
    return f"{inteiro},{centavos}"


def _datas(inicio: date, n: int) -> list[date]:
    """n datas aleatórias dentro do mês que começa em `inicio`."""
    return [inicio + timedelta(days=random.randint(0, 27)) for _ in range(n)]


# ---------------------------------------------------------------------------
# Arquivo 1 — Janeiro: valores em padrão BR (texto), coluna "Data da Venda"
# ---------------------------------------------------------------------------
def gerar_janeiro() -> None:
    n = 12
    df = pd.DataFrame(
        {
            "Data da Venda": _datas(date(2025, 1, 1), n),
            "Produto": [random.choice(PRODUTOS) for _ in range(n)],
            "Qtd": [random.randint(1, 20) for _ in range(n)],
            # valor como TEXTO no padrão brasileiro -> "1.200,50"
            "Valor Total": [_valor_br(random.uniform(10, 1500)) for _ in range(n)],
        }
    )
    df.to_excel(PASTA / "vendas_janeiro.xlsx", index=False)


# ---------------------------------------------------------------------------
# Arquivo 2 — Fevereiro: coluna "DT", valores US (float), nomes com espaços
# ---------------------------------------------------------------------------
def gerar_fevereiro() -> None:
    n = 10
    df = pd.DataFrame(
        {
            "DT": _datas(date(2025, 2, 1), n),
            # espaços extras e capitalização aleatória no nome do produto
            "produto ": [
                f"  {random.choice(PRODUTOS).upper()}  " for _ in range(n)
            ],
            "quantidade": [random.randint(1, 20) for _ in range(n)],
            # valor como número US (ponto decimal)
            "valor": [round(random.uniform(10, 1500), 2) for _ in range(n)],
        }
    )
    df.to_excel(PASTA / "vendas_fevereiro.xlsx", index=False)


# ---------------------------------------------------------------------------
# Arquivo 3 — Março: CSV com separador ";", coluna "data", células vazias
# ---------------------------------------------------------------------------
def gerar_marco() -> None:
    n = 11
    valores = [_valor_br(random.uniform(10, 1500)) for _ in range(n)]
    qtds: list[object] = [random.randint(1, 20) for _ in range(n)]
    # apaga alguns valores de propósito (células vazias)
    qtds[2] = ""
    valores[5] = ""
    df = pd.DataFrame(
        {
            "data": _datas(date(2025, 3, 1), n),
            "produto": [random.choice(PRODUTOS) for _ in range(n)],
            "qtd": qtds,
            "valor total": valores,
        }
    )
    # sep=";" e decimal="," é o padrão de CSV "exportado do Excel" no Brasil
    df.to_csv(PASTA / "vendas_marco.csv", index=False, sep=";", encoding="utf-8")


# ---------------------------------------------------------------------------
# Arquivo 4 — Abril: DUAS abas (uma de dados + uma de "Rascunho" com lixo)
# ---------------------------------------------------------------------------
def gerar_abril() -> None:
    n = 9
    vendas = pd.DataFrame(
        {
            "Data": _datas(date(2025, 4, 1), n),
            "Produto": [random.choice(PRODUTOS) for _ in range(n)],
            "Quantidade": [random.randint(1, 20) for _ in range(n)],
            "Preco": [round(random.uniform(10, 1500), 2) for _ in range(n)],
        }
    )
    # aba "Rascunho": anotações soltas que NÃO são dados de venda
    rascunho = pd.DataFrame(
        {
            "obs": [
                "conferir total com o Bruno",
                "nota fiscal 12345 pendente",
                "",
                "ligar pro fornecedor",
            ]
        }
    )
    with pd.ExcelWriter(PASTA / "vendas_abril.xlsx") as writer:
        vendas.to_excel(writer, sheet_name="Vendas", index=False)
        rascunho.to_excel(writer, sheet_name="Rascunho", index=False)


# ---------------------------------------------------------------------------
# Arquivo 5 — Maio: colunas com acento/maiúsculas, linhas totalmente vazias,
#             e uma coluna extra ("Região") que não existe nos outros arquivos
# ---------------------------------------------------------------------------
def gerar_maio() -> None:
    n = 10
    df = pd.DataFrame(
        {
            "Data": _datas(date(2025, 5, 1), n),
            "Produto": [random.choice(PRODUTOS) for _ in range(n)],
            "Quantidade": [random.randint(1, 20) for _ in range(n)],
            "Preço Unitário": [round(random.uniform(10, 1500), 2) for _ in range(n)],
            "Região": [random.choice(["Sul", "Sudeste", "Nordeste"]) for _ in range(n)],
        }
    )
    # insere 2 linhas totalmente vazias no meio (ruído comum em planilhas)
    vazia = pd.DataFrame([{c: None for c in df.columns}])
    df = pd.concat(
        [df.iloc[:4], vazia, df.iloc[4:7], vazia, df.iloc[7:]], ignore_index=True
    )
    df.to_excel(PASTA / "vendas_maio.xlsx", index=False)


def main() -> None:
    gerar_janeiro()
    gerar_fevereiro()
    gerar_marco()
    gerar_abril()
    gerar_maio()
    print("Arquivos de exemplo gerados em:", PASTA)
    for arquivo in sorted(PASTA.glob("vendas_*")):
        print("  -", arquivo.name)


if __name__ == "__main__":
    main()
