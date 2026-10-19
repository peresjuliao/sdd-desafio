"""Serialização do resultado (spec 4.2). Centavos viram reais com 2 casas só aqui."""
import json

from .motor import Resultado


def _reais(c: int) -> float:
    return c / 100


def para_dict(r: Resultado) -> dict:
    return {
        "politica": r.politica,
        "colaborador": r.pedido.colaborador,
        "periodo": r.pedido.periodo,
        "itens": [{
            "id": a.despesa.id,
            "data": a.despesa.data.isoformat(),
            "categoria": a.despesa.categoria,
            "descricao": a.despesa.descricao,
            "moeda": a.despesa.moeda,
            "valor_original": _reais(a.despesa.valor),
            "taxa_cambio": None if a.taxa is None else float(a.taxa),
            "valor_solicitado": None if a.valor_brl is None else _reais(a.valor_brl),
            "valor_reembolsavel": _reais(a.reembolsavel),
            "status": a.status,
            "motivo": a.motivo,
            "detalhe": a.detalhe,
        } for a in r.avaliacoes],
        "resumo": {k: (_reais(v) if k.startswith("total") else v) for k, v in r.resumo.items()},
    }


def escrever(r: Resultado, caminho) -> None:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(para_dict(r), f, ensure_ascii=False, indent=2)
        f.write("\n")
