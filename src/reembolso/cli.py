"""CLI: reembolso calcular --input despesas.json --output resultado.json"""
import argparse
import sys

from .entrada import EntradaInvalida, ler_pedido
from .motor import calcular
from .politica import POLITICA_V3
from .saida import escrever


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="reembolso")
    sub = parser.add_subparsers(dest="comando", required=True)
    calc = sub.add_parser("calcular", help="calcula o reembolso de um arquivo de despesas")
    calc.add_argument("--input", required=True)
    calc.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        resultado = calcular(ler_pedido(args.input), POLITICA_V3)
    except EntradaInvalida as e:
        print(f"erro na entrada: {e}", file=sys.stderr)
        return 2
    escrever(resultado, args.output)   # só abre a saída depois do cálculo (DT-004)
    r = resultado.resumo
    print(f"{len(resultado.avaliacoes)} itens: {r['aprovados']} aprovados, {r['parciais']} parciais, "
          f"{r['recusados']} recusados; reembolsavel R$ {r['total_reembolsavel'] / 100:.2f}")
    return 0
