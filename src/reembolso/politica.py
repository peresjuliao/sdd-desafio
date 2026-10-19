"""Política de reembolso como dados (plan seção 4). Valores em centavos.

Forma: {"versao", "limites" (tabela padrão: categoria -> centavos),
        "centros_custo" (cc -> categoria -> centavos), "nota_fiscal_obrigatoria_acima_de",
        "acrescimo_em_viagem_percentual"}
"""
import json

from .entrada import EntradaInvalida, centavos

POLITICA_PADRAO = {
    "versao": "v3",
    "limites": {"alimentacao": 6000, "transporte_urbano": 8000, "hospedagem": 25000},
    "centros_custo": {},
    "nota_fiscal_obrigatoria_acima_de": 10000,
    "acrescimo_em_viagem_percentual": 50,
}
POLITICA_V3 = POLITICA_PADRAO  # nome usado pelos testes da fase 1


def _tabela(limites: dict) -> dict:
    """categoria -> centavos; ignora periodicidade/observacao (AMB-028)."""
    return {str(cat).strip().lower(): centavos(spec["limite"]) for cat, spec in limites.items()}


def carregar_politica(caminho) -> dict:
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
        return {
            "versao": str(dados.get("versao", "?")),
            "limites": _tabela(dados["padrao"]),
            "centros_custo": {cc: _tabela(t) for cc, t in dados.get("centros_custo", {}).items()},
            "nota_fiscal_obrigatoria_acima_de": centavos(dados.get("nota_fiscal_obrigatoria_acima_de", 100)),
            "acrescimo_em_viagem_percentual": int(dados.get("acrescimo_em_viagem_percentual", 50)),
        }
    except (OSError, json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
        raise EntradaInvalida(f"politica invalida em {caminho}: {e!r}")


def limites_para(politica: dict, centro_custo) -> dict:
    """RN-013: padrão sobreposta, categoria a categoria, pela entrada do centro de custo."""
    return {**politica["limites"], **politica["centros_custo"].get(centro_custo or "", {})}
