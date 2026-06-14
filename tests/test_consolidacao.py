"""Testes da consolidação — junção de fontes heterogêneas e descarte de lixo."""

import pandas as pd
import pytest

from consolidador.consolidacao import ErroConsolidacao, consolidar
from consolidador.leitor import Planilha


def _planilha(dados: dict, arquivo: str, aba: str | None = None) -> Planilha:
    return Planilha(df=pd.DataFrame(dados), arquivo=arquivo, aba=aba)


def test_consolida_e_carimba_origem():
    planilhas = [
        _planilha({"Produto": ["Café 500g"], "Valor": ["10,00"]}, "jan.xlsx", "Sheet1"),
        _planilha({"produto": ["Arroz 5kg"], "valor": ["20.00"]}, "fev.csv"),
    ]
    resultado = consolidar(planilhas)
    assert len(resultado.dados) == 2
    assert set(resultado.dados["origem"]) == {"jan.xlsx[Sheet1]", "fev.csv"}


def test_descarta_planilha_sem_colunas_essenciais():
    planilhas = [
        _planilha({"Produto": ["Café 500g"], "Valor": ["10,00"]}, "vendas.xlsx", "Vendas"),
        _planilha({"obs": ["anotação solta"]}, "vendas.xlsx", "Rascunho"),
    ]
    resultado = consolidar(planilhas)
    assert len(resultado.dados) == 1
    assert resultado.descartadas == ["vendas.xlsx[Rascunho]"]


def test_alinha_colunas_que_existem_so_em_alguns_arquivos():
    planilhas = [
        _planilha({"Produto": ["Café 500g"], "Valor": ["10,00"], "Região": ["Sul"]}, "a.xlsx"),
        _planilha({"Produto": ["Arroz 5kg"], "Valor": ["20,00"]}, "b.xlsx"),
    ]
    resultado = consolidar(planilhas)
    assert "regiao" in resultado.dados.columns
    # quem não tinha 'regiao' fica com NaN, sem quebrar a junção
    assert resultado.dados["regiao"].isna().sum() == 1


def test_erro_quando_nenhuma_planilha_tem_dados_de_venda():
    planilhas = [_planilha({"obs": ["só lixo"]}, "lixo.xlsx", "Rascunho")]
    with pytest.raises(ErroConsolidacao):
        consolidar(planilhas)


def test_ordem_das_colunas_e_amigavel():
    planilhas = [
        _planilha(
            {"Valor": ["10,00"], "Produto": ["Café 500g"], "Qtd": ["2"], "Data": ["2025-01-01"]},
            "a.xlsx",
        )
    ]
    resultado = consolidar(planilhas)
    assert list(resultado.dados.columns) == ["data", "produto", "quantidade", "valor", "origem"]
