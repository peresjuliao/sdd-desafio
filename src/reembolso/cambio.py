"""Tabela de câmbio (RN-014): data -> moeda -> reais por unidade."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import json

from .entrada import EntradaInvalida

SEM_CAMBIO = {"taxas": {}}


def carregar_cambio(caminho) -> dict:
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
        taxas = {date.fromisoformat(dia): {m.strip().upper(): Decimal(str(t)) for m, t in moedas.items()}
                 for dia, moedas in dados["taxas"].items()}
        return {"taxas": dict(sorted(taxas.items()))}
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, AttributeError) as e:
        raise EntradaInvalida(f"cambio invalido em {caminho}: {e!r}")


def taxa_para(cambio: dict, moeda: str, dia: date):
    """Taxa da data ou, se não publicada, a mais recente anterior (AMB-019). None se não há."""
    if moeda == "BRL":
        return Decimal(1)
    taxa = None
    for d, moedas in cambio["taxas"].items():   # ordenado por data
        if d > dia:
            break
        if moeda in moedas:
            taxa = moedas[moeda]
    return taxa


def converter(valor_centavos: int, taxa: Decimal) -> int:
    """AMB-021: centavos × taxa, arredondado a centavos uma vez, meio para cima."""
    return int((Decimal(valor_centavos) * taxa).quantize(Decimal(1), rounding=ROUND_HALF_UP))
