# Consolidador Automático de Relatórios

[![CI](https://github.com/david-oliveira-dev/consolidador-relatorios/actions/workflows/ci.yml/badge.svg)](https://github.com/david-oliveira-dev/consolidador-relatorios/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Transforme dezenas de planilhas bagunçadas em um relatório único, limpo e apresentável — em segundos, com um comando.**

---

## Antes / Depois

| Antes 😩 | Depois 🎉 |
|---|---|
| Vários arquivos Excel/CSV, abas soltas, colunas com nomes diferentes (`Data`, `DT`, `data da venda`), números em formatos misturados (`1.200,50` e `1200.5`), células vazias e linhas em branco. | Um Excel formatado com aba de dados + resumo + gráfico, **e** um PDF executivo de 1 página com os números-chave. |

<!-- Cole aqui 2 prints: (1) as planilhas bagunçadas, (2) o relatório final limpo -->

| Planilhas de entrada | Relatório gerado |
|---|---|
| _(print das planilhas bagunçadas aqui)_ | _(print do relatório/PDF aqui)_ |

---

## O problema de negócio

Pequenas empresas, contadores e equipes recebem dados de venda em **várias planilhas inconsistentes** todo mês e gastam horas consolidando tudo na mão — copiando, colando, corrigindo formato de data e número, somando por produto. É repetitivo, lento e cheio de erro humano.

Esta ferramenta faz esse trabalho em segundos: lê uma pasta, limpa, consolida e gera o relatório final pronto para apresentar.

---

## Como rodar

Pré-requisito: **Python 3.11+**.

```bash
# 1. Clonar e entrar na pasta
git clone <url-do-repositorio>
cd consolidador-relatorios

# 2. Criar e ativar o ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Instalar
pip install -e .

# 4. Rodar com os dados de exemplo (já incluídos)
consolidador --entrada ./dados_exemplo --saida ./saida
```

Os relatórios aparecem em `saida/`:
- `relatorio_consolidado.xlsx` — Excel com abas **Dados** e **Resumo** + gráfico.
- `resumo_executivo.pdf` — PDF de 1 página com os KPIs.

Para usar com seus próprios arquivos, basta apontar `--entrada` para a sua pasta:

```bash
consolidador --entrada /caminho/das/minhas/planilhas --saida ./saida
```

> Quer regenerar as planilhas de exemplo? `python dados_exemplo/_gerar_dados.py`

---

## Como funciona

O processamento acontece em fases independentes (cada uma é um módulo em `src/consolidador/`):

1. **Leitura** (`leitor.py`) — varre a pasta, lê `.xlsx`/`.xls`/`.csv` e **todas as abas**, registrando a origem de cada tabela.
2. **Limpeza** (`limpeza.py`) — padroniza nomes de coluna (sem acento/maiúscula/espaço), mapeia colunas equivalentes para um nome canônico (configurável), normaliza datas e números (BR e US) e remove linhas vazias.
3. **Consolidação** (`consolidacao.py`) — junta tudo num único conjunto de dados, alinha colunas que só existem em alguns arquivos e descarta abas que não são de venda.
4. **Relatório Excel** (`relatorio.py`) — gera o `.xlsx` formatado com resumo por produto e por mês + gráfico.
5. **PDF executivo** (`resumo_pdf.py`) — monta a página única com KPIs e gráfico.
6. **CLI** (`cli.py`) — amarra tudo num comando amigável, com barra de progresso e erros claros.

---

## Stack e decisões

| Ferramenta | Por quê |
|---|---|
| **pandas** | Manipulação e agregação de dados tabulares — o padrão da indústria. |
| **openpyxl** | Ler/escrever Excel e gerar gráfico **nativo** (editável dentro do arquivo). |
| **matplotlib** | PDF executivo vetorial (nítido em qualquer zoom) com uma só ferramenta. |
| **typer** | CLI baseada em type hints, com `--help` e validação automáticos. |
| **rich** | Barra de progresso e mensagens bonitas no terminal. |
| **pytest** | Testes nos pontos mais quebráveis (limpeza e consolidação). |

Outras escolhas: layout `src/` (evita imports acidentais), mapeamento de colunas **configurável** (cada cliente tem o seu) e mensagens de erro em português pensadas para usuário não-técnico.

---

## Testes

```bash
pip install -e ".[dev]"
pytest
```

---

## Próximos passos

- Interface web (upload da pasta pelo navegador).
- Agendamento automático (rodar todo dia 1 do mês).
- Configuração do mapeamento de colunas por arquivo `.yaml`, sem mexer no código.
- Suporte a mais formatos (Google Sheets, `.ods`).
