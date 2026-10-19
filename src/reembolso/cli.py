"""CLI: reembolso calcular --input despesas.json --output resultado.json"""
import argparse
import sys

from .cambio import SEM_CAMBIO, carregar_cambio
from .entrada import EntradaInvalida, ler_pedido
from .motor import calcular
from .politica import POLITICA_PADRAO, carregar_politica
from .saida import escrever


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="reembolso")
    sub = parser.add_subparsers(dest="comando", required=True)
    calc = sub.add_parser("calcular", help="calcula o reembolso de um arquivo de despesas")
    calc.add_argument("--input", required=True)
    calc.add_argument("--output", required=True)
    calc.add_argument("--politica", help="tabela de limites (ex.: exemplos/envelope/politica-v4.json); sem ela vale a padrão")
    calc.add_argument("--cambio", help="taxas de câmbio (ex.: exemplos/envelope/cambio.json); sem ela só BRL é aceito")
    args = parser.parse_args(argv)
    try:
        politica = carregar_politica(args.politica) if args.politica else POLITICA_PADRAO
        cambio = carregar_cambio(args.cambio) if args.cambio else SEM_CAMBIO
        resultado = calcular(ler_pedido(args.input), politica, cambio)
    except EntradaInvalida as e:
        print(f"erro na entrada: {e}", file=sys.stderr)
        return 2
    escrever(resultado, args.output)   # só abre a saída depois do cálculo (DT-004)
    r = resultado.resumo
    print(f"{len(resultado.avaliacoes)} itens: {r['aprovados']} aprovados, {r['parciais']} parciais, "
          f"{r['recusados']} recusados, {r['pendentes']} pendentes; reembolsavel R$ {r['total_reembolsavel'] / 100:.2f}"
          f", pendente R$ {r['total_pendente'] / 100:.2f}")
    return 0
