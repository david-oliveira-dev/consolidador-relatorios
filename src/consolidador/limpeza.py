"""Limpeza e padronização dos dados crus.

Cada função aqui resolve UM tipo de sujeira comum em planilhas do mundo real.
São pequenas e independentes de propósito: facilita entender, testar e ajustar.

Fluxo (função `limpar_dataframe`):
    1. normaliza nomes de coluna (minúsculo, sem acento, sem espaço)
    2. mapeia colunas equivalentes para um nome canônico (configurável)
    3. remove linhas totalmente vazias
    4. converte a coluna de data para datetime
    5. converte colunas numéricas (BR "1.200,50" e US "1200.5") para float
    6. padroniza o texto das colunas de produto/categoria
"""

from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuração (o usuário avançado pode sobrescrever ao chamar limpar_dataframe)
# ---------------------------------------------------------------------------

# Mapeia o nome JÁ NORMALIZADO da coluna -> nome canônico.
# É aqui que dizemos que "dt", "data" e "data_da_venda" são a mesma coisa.
MAPEAMENTO_CANONICO: dict[str, str] = {
    "data": "data",
    "data_da_venda": "data",
    "dt": "data",
    "produto": "produto",
    "qtd": "quantidade",
    "quantidade": "quantidade",
    "valor": "valor",
    "valor_total": "valor",
    "preco": "valor",
    "preco_unitario": "valor",
    "regiao": "regiao",
}

# Quais colunas canônicas são de data e quais são numéricas.
COLUNAS_DATA = {"data"}
COLUNAS_NUMERICAS = {"quantidade", "valor"}


# ---------------------------------------------------------------------------
# 1) Nomes de coluna
# ---------------------------------------------------------------------------
def normalizar_nome_coluna(nome: str) -> str:
    """Padroniza um nome de coluna: minúsculo, sem acento, sem espaço extra.

    Exemplos:
        'Data da Venda'  -> 'data_da_venda'
        ' produto '      -> 'produto'
        'Preço Unitário' -> 'preco_unitario'
    """
    texto = str(nome).strip().lower()
    # NFKD separa a letra do acento; descartamos os caracteres de acento.
    texto = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))
    texto = re.sub(r"\s+", "_", texto.strip())  # espaços -> underscore
    texto = re.sub(r"[^a-z0-9_]", "", texto)  # remove o que não for letra/dígito/_
    texto = re.sub(r"_+", "_", texto).strip("_")  # colapsa underscores repetidos
    return texto


def padronizar_colunas(df: pd.DataFrame, mapeamento: dict[str, str] | None = None) -> pd.DataFrame:
    """Normaliza os nomes e aplica o mapeamento canônico.

    Colunas desconhecidas (fora do mapeamento) mantêm o nome normalizado, em
    vez de serem descartadas — preferimos não perder dados silenciosamente.
    """
    mapeamento = MAPEAMENTO_CANONICO if mapeamento is None else mapeamento
    novos_nomes = {}
    for coluna in df.columns:
        normalizado = normalizar_nome_coluna(coluna)
        novos_nomes[coluna] = mapeamento.get(normalizado, normalizado)
    return df.rename(columns=novos_nomes)


# ---------------------------------------------------------------------------
# 2) Números (BR x US)
# ---------------------------------------------------------------------------
def converter_numero(valor: object) -> float:
    """Converte texto numérico para float, lidando com padrões BR e US.

    Regras (heurística):
        "1.200,50" (vírgula E ponto) -> BR: ponto é milhar, vírgula é decimal
        "57,83"    (só vírgula)      -> BR: vírgula é decimal
        "1096.40"  (só ponto)        -> US: ponto é decimal
        "" / None / inválido         -> NaN
    """
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return np.nan
    texto = str(valor).strip()
    if texto == "" or texto.lower() in {"nan", "none"}:
        return np.nan

    tem_virgula = "," in texto
    tem_ponto = "." in texto
    if tem_virgula and tem_ponto:
        texto = texto.replace(".", "").replace(",", ".")  # padrão brasileiro
    elif tem_virgula:
        texto = texto.replace(",", ".")  # vírgula decimal isolada

    try:
        return float(texto)
    except ValueError:
        return np.nan


# ---------------------------------------------------------------------------
# 3) Datas
# ---------------------------------------------------------------------------
def converter_datas(serie: pd.Series) -> pd.Series:
    """Converte uma coluna para datetime; valores inválidos viram NaT.

    errors='coerce' garante que uma data esquisita não derrube o processo
    inteiro — vira NaT (Not a Time) e segue o jogo.
    """
    return pd.to_datetime(serie, errors="coerce", dayfirst=False)


# ---------------------------------------------------------------------------
# 4) Texto (produtos, categorias)
# ---------------------------------------------------------------------------
def padronizar_texto(serie: pd.Series) -> pd.Series:
    """Tira espaços extras e uniformiza a capitalização do texto.

    strip + colapsa espaços internos + .title() faz '  CAFÉ 500G  ' e
    'Café 500g' virarem o MESMO 'Café 500G' — essencial para somar/agrupar
    o mesmo produto escrito de formas diferentes.
    """

    def _limpar(v: object) -> object:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return v
        texto = re.sub(r"\s+", " ", str(v).strip())
        return texto.title()

    return serie.map(_limpar)


# ---------------------------------------------------------------------------
# 5) Linhas vazias
# ---------------------------------------------------------------------------
def remover_linhas_vazias(df: pd.DataFrame) -> pd.DataFrame:
    """Remove linhas em que TODAS as células estão vazias (how='all')."""
    # Strings vazias não contam como NaN para o dropna, então tratamos antes.
    limpo = df.replace(r"^\s*$", np.nan, regex=True)
    return limpo.dropna(how="all").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------------
def limpar_dataframe(df: pd.DataFrame, mapeamento: dict[str, str] | None = None) -> pd.DataFrame:
    """Aplica todas as etapas de limpeza e devolve um DataFrame padronizado."""
    df = padronizar_colunas(df, mapeamento)
    df = remover_linhas_vazias(df)

    for coluna in df.columns:
        if coluna in COLUNAS_DATA:
            df[coluna] = converter_datas(df[coluna])
        elif coluna in COLUNAS_NUMERICAS:
            df[coluna] = df[coluna].map(converter_numero)
        else:
            # demais colunas são tratadas como texto (produto, regiao, ...).
            # Obs.: no pandas 3.0 texto tem dtype 'str' (não mais 'object'),
            # então não dá para filtrar por dtype == object aqui.
            df[coluna] = padronizar_texto(df[coluna])

    return df
