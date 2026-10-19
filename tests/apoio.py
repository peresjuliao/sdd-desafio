"""Helpers dos testes: construir pedidos pequenos sem repetir o JSON inteiro."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from reembolso.entrada import montar_pedido  # noqa: E402


def despesa(**kw):
    base = {"id": "x", "data": "2026-07-10", "categoria": "alimentacao",
            "descricao": "", "fornecedor": "F", "valor": 10.0, "tem_nota_fiscal": True}
    base.update(kw)
    return base


def pedido(*despesas, inicio="2026-07-01", fim="2026-07-31"):
    return montar_pedido({
        "colaborador": {"id": "c-1", "nome": "Teste", "centro_custo": "CC-X"},
        "periodo": {"competencia": inicio[:7], "inicio": inicio, "fim": fim},
        "despesas": [dict(d, id=d.get("id") if d.get("id") != "x" else f"d-{i+1}")
                     for i, d in enumerate(despesas)],
    })
