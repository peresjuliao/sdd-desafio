"""T-014: pendência de aprovação manual (RN-015)."""
import os, unittest
from apoio import pedido, despesa
from reembolso.motor import calcular
from reembolso.politica import carregar_politica

V4 = carregar_politica(os.path.join(os.path.dirname(__file__), "..", "exemplos", "envelope", "politica-v4.json"))


def comercial(*despesas):
    p = pedido(*despesas); p.colaborador["centro_custo"] = "CC-COMERCIAL"
    return calcular(p, V4)


class TestPendencia(unittest.TestCase):
    def test_rn_015_acima_de_500_fica_pendente(self):
        r = comercial(despesa(categoria="hospedagem", data="2026-07-22", valor=1200))
        a, = r.avaliacoes
        self.assertEqual((a.reembolsavel, a.status, a.motivo), (60000, "pendente", "acima_do_limite_diario"))
        self.assertIn("aguarda gestor", a.detalhe)

    def test_b_24_exatamente_500_aprovado(self):
        a, = comercial(despesa(categoria="hospedagem", data="2026-07-22", valor=500)).avaliacoes
        self.assertEqual((a.reembolsavel, a.status), (50000, "aprovado"))

    def test_b_25_um_centavo_acima_pendente(self):
        a, = comercial(despesa(categoria="hospedagem", data="2026-07-22", valor=500.01)).avaliacoes
        self.assertEqual(a.status, "pendente")

    def test_rn_012_pendente_fora_do_total_reembolsavel(self):
        r = comercial(despesa(categoria="hospedagem", data="2026-07-22", valor=1200),
                      despesa(data="2026-07-23", valor=95, fornecedor="G"))
        self.assertEqual(r.resumo["total_reembolsavel"], 9500)
        self.assertEqual(r.resumo["total_pendente"], 60000)
        self.assertEqual((r.resumo["pendentes"], r.resumo["aprovados"]), (1, 1))


if __name__ == "__main__":
    unittest.main()
