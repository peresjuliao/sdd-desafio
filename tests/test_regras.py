import unittest
from apoio import pedido, despesa
from reembolso.motor import calcular
from reembolso.politica import POLITICA_V3


def avaliar(*despesas, **kw):
    return calcular(pedido(*despesas, **kw), POLITICA_V3).avaliacoes


class TestFundacao(unittest.TestCase):
    def test_rn_012_resumo_soma_e_conta(self):
        r = calcular(pedido(despesa(valor=10), despesa(valor=20.5, data="2026-07-11")), POLITICA_V3)
        self.assertEqual(r.resumo["total_solicitado"], 3050)
        self.assertEqual(r.resumo["total_reembolsavel"], 3050)
        self.assertEqual(r.resumo["aprovados"], 2)
        self.assertEqual(r.resumo["recusados"], 0)
        self.assertEqual([a.despesa.id for a in r.avaliacoes], ["d-1", "d-2"])

    def test_b_13_sem_despesas(self):
        r = calcular(pedido(), POLITICA_V3)
        self.assertEqual(r.avaliacoes, [])
        self.assertEqual(r.resumo["total_reembolsavel"], 0)


if __name__ == "__main__":
    unittest.main()
