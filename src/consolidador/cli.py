"""Ponto de entrada do terminal: o comando `consolidador`.

Amarra todas as fases (ler -> consolidar -> Excel -> PDF) num único comando
amigável, com barra de progresso (rich) e mensagens de erro claras em
português, pensadas para um usuário não-técnico.

Uso:
    consolidador --entrada ./dados_exemplo --saida ./saida
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn

from consolidador.consolidacao import ErroConsolidacao, consolidar
from consolidador.leitor import ErroLeitura, ler_pasta
from consolidador.relatorio import gerar_relatorio_excel
from consolidador.resumo_pdf import gerar_resumo_pdf

app = typer.Typer(
    add_completion=False,
    help="Lê uma pasta de planilhas bagunçadas e gera um relatório único e limpo.",
)
console = Console()

NOME_EXCEL = "relatorio_consolidado.xlsx"
NOME_PDF = "resumo_executivo.pdf"


@app.command()
def main(
    entrada: Path = typer.Option(
        ...,
        "--entrada",
        "-e",
        help="Pasta com as planilhas a consolidar (.xlsx, .xls, .csv).",
    ),
    saida: Path = typer.Option(
        Path("saida"),
        "--saida",
        "-s",
        help="Pasta onde os relatórios serão salvos.",
    ),
) -> None:
    """Consolida as planilhas da pasta de ENTRADA e gera relatório na SAÍDA."""
    console.print(
        Panel.fit(
            "[bold]Consolidador Automático de Relatórios[/bold]\n"
            f"Entrada: [cyan]{entrada}[/cyan]   Saída: [cyan]{saida}[/cyan]",
            border_style="blue",
        )
    )

    try:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            tarefa = progress.add_task("Lendo planilhas...", total=4)

            planilhas = ler_pasta(entrada)
            progress.advance(tarefa)

            progress.update(tarefa, description="Limpando e consolidando...")
            resultado = consolidar(planilhas)
            progress.advance(tarefa)

            progress.update(tarefa, description="Gerando relatório Excel...")
            caminho_excel = gerar_relatorio_excel(resultado.dados, saida / NOME_EXCEL)
            progress.advance(tarefa)

            progress.update(tarefa, description="Gerando PDF executivo...")
            caminho_pdf = gerar_resumo_pdf(resultado.dados, saida / NOME_PDF)
            progress.advance(tarefa)

    except (ErroLeitura, ErroConsolidacao) as erro:
        # Erros esperados, já com mensagem amigável: mostra e encerra sem stacktrace.
        console.print(f"\n[bold red]✗ Não foi possível concluir:[/bold red] {erro}")
        raise typer.Exit(code=1)
    except Exception as erro:  # noqa: BLE001 — rede de segurança
        console.print(
            f"\n[bold red]✗ Ocorreu um erro inesperado:[/bold red] {erro}\n"
            "Se o problema persistir, verifique se os arquivos não estão abertos "
            "em outro programa."
        )
        raise typer.Exit(code=1)

    # --- Resumo final ---
    df = resultado.dados
    linhas = [
        f"[green]✓[/green] [bold]{len(df)}[/bold] registros consolidados de "
        f"[bold]{df['origem'].nunique()}[/bold] fonte(s)",
    ]
    if resultado.descartadas:
        ignoradas = ", ".join(resultado.descartadas)
        linhas.append(f"[yellow]•[/yellow] Ignoradas (sem dados de venda): {ignoradas}")
    linhas.append(f"[green]✓[/green] Excel: [cyan]{caminho_excel}[/cyan]")
    linhas.append(f"[green]✓[/green] PDF:   [cyan]{caminho_pdf}[/cyan]")

    console.print(
        Panel("\n".join(linhas), title="Concluído", border_style="green")
    )


if __name__ == "__main__":
    app()
