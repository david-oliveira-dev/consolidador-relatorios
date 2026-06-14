"""Testes da limpeza — o ponto onde a maioria dos bugs de dados aparece."""

import math

import pandas as pd
import pytest

from consolidador.limpeza import (
    converter_datas,
    converter_numero,
    limpar_dataframe,
    normalizar_nome_coluna,
    padronizar_colunas,
    padronizar_texto,
    remover_linhas_vazias,
)


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("Data da Venda", "data_da_venda"),
        (" produto ", "produto"),
        ("Preço Unitário", "preco_unitario"),
        ("DT", "dt"),
        ("Valor  Total", "valor_total"),
    ],
)
def test_normalizar_nome_coluna(entrada, esperado):
    assert normalizar_nome_coluna(entrada) == esperado


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("1.200,50", 1200.50),  # BR: ponto milhar, vírgula decimal
        ("57,83", 57.83),  # BR: só vírgula decimal
        ("1096.40", 1096.40),  # US: ponto decimal
        ("1.147,61", 1147.61),
    ],
)
def test_converter_numero_validos(entrada, esperado):
    assert converter_numero(entrada) == pytest.approx(esperado)


@pytest.mark.parametrize("entrada", ["", "  ", None, "abc", "nan"])
def test_converter_numero_invalidos_viram_nan(entrada):
    assert math.isnan(converter_numero(entrada))


def test_converter_datas_invalida_vira_nat():
    serie = pd.Series(["2025-01-15", "data ruim", None])
    resultado = converter_datas(serie)
    assert resultado.iloc[0] == pd.Timestamp("2025-01-15")
    assert pd.isna(resultado.iloc[1])
    assert pd.isna(resultado.iloc[2])


def test_padronizar_colunas_mapeia_para_canonico():
    df = pd.DataFrame(columns=["DT", "Qtd", "Valor Total", "Preço Unitário"])
    resultado = padronizar_colunas(df)
    assert list(resultado.columns) == ["data", "quantidade", "valor", "valor"]


def test_padronizar_colunas_mantem_desconhecida_normalizada():
    df = pd.DataFrame(columns=["Coluna Estranha"])
    assert list(padronizar_colunas(df).columns) == ["coluna_estranha"]


def test_padronizar_colunas_aceita_mapeamento_customizado():
    df = pd.DataFrame(columns=["vlr"])
    resultado = padronizar_colunas(df, mapeamento={"vlr": "valor"})
    assert list(resultado.columns) == ["valor"]


def test_padronizar_texto_uniformiza_caixa_e_espacos():
    serie = pd.Series(["  CAFÉ 500G  ", "café 500g", "Café 500g"])
    resultado = padronizar_texto(serie)
    # os três viram o mesmo valor -> agrupam corretamente depois
    assert resultado.nunique() == 1
    assert resultado.iloc[0] == "Café 500G"


def test_remover_linhas_totalmente_vazias():
    df = pd.DataFrame({"a": [1, None, 3, ""], "b": ["x", None, "z", "  "]})
    resultado = remover_linhas_vazias(df)
    # remove a linha toda-None e a linha com strings vazias/espaços
    assert len(resultado) == 2


def test_limpar_dataframe_integra_tudo():
    """Um mini-DataFrame bagunçado deve sair limpo e padronizado."""
    df = pd.DataFrame(
        {
            "DT": ["2025-01-10", None],
            "produto ": ["  CAFÉ 500G  ", "Café 500g"],
            "Qtd": ["5", "3"],
            "Valor Total": ["1.200,50", "57,83"],
        }
    )
    limpo = limpar_dataframe(df)
    assert list(limpo.columns) == ["data", "produto", "quantidade", "valor"]
    assert limpo["valor"].tolist() == [1200.50, 57.83]
    assert limpo["produto"].nunique() == 1  # mesmo produto após padronizar
    assert limpo["data"].iloc[0] == pd.Timestamp("2025-01-10")
