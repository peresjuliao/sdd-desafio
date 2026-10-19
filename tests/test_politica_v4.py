"""T-012: política lida de arquivo e limites por centro de custo (RN-013)."""
import os, unittest
from apoio import pedido, despesa
from reembolso.motor import calcular
from reembolso.politica import carregar_politica, limites_para, POLITICA_PADRAO

V4 = carregar_politica(os.path.join(os.path.dirname(__file__), "..", "exemplos", "envelope", "politica-v4.json"))


def avaliar(cc, *despesas, politica=V4):
    p = pedido(*despesas)
    p.colaborador["centro_custo"] = cc
    return calcular(p, politica).avaliacoes


class TestPoliticaV4(unittest.TestCase):
    def test_carrega_arquivo_em_centavos(self):
        self.assertEqual(V4["versao"], "v4")
        self.assertEqual(V4["limites"], {"alimentacao": 6000, "transporte_urbano": 8000, "hospedagem": 25000})
        self.assertEqual(V4["centros_custo"]["CC-COMERCIAL"]["representacao"], 30000)
        self.assertEqual(V4["nota_fiscal_obrigatoria_acima_de"], 10000)

    def test_rn_013_cc_sem_entrada_usa_padrao(self):
        self.assertEqual(limites_para(V4, "CC-SUPORTE-N2"), V4["limites"])
        self.assertEqual(limites_para(V4, None), V4["limites"])  # B-16

    def test_rn_013_cc_sobrepoe_categoria_a_categoria(self):
        adm = limites_para(V4, "CC-ADM")
        self.assertEqual(adm["alimentacao"], 4500)
        self.assertEqual(adm["hospedagem"], 25000)  # B-17: padrão supre
        a, = avaliar("CC-ADM", despesa(categoria="hospedagem", valor=200))
        self.assertEqual((a.reembolsavel, a.status), (20000, "aprovado"))

    def test_rn_013_limite_zero_e_categoria_nao_coberta(self):
        a, = avaliar("CC-ENG-PLATAFORMA", despesa(categoria="hospedagem", valor=200))
        self.assertEqual((a.status, a.motivo), ("recusado", "categoria_nao_coberta"))

    def test_b_18_hospedagem_limite_zero_ainda_marca_viagem(self):
        h, almoco = avaliar("CC-ENG-PLATAFORMA", despesa(categoria="hospedagem", valor=200),
                            despesa(valor=100, fornecedor="G"))
        self.assertEqual(h.motivo, "categoria_nao_coberta")
        self.assertEqual(almoco.reembolsavel, 7500 * 150 // 100)  # 75 * 1,5 = 112,50 → paga 100

    def test_rn_013_representacao_so_onde_listada(self):
        a, = avaliar("CC-COMERCIAL", despesa(categoria="representacao", valor=340))
        self.assertEqual((a.reembolsavel, a.status), (30000, "parcial"))
        b, = avaliar("CC-SUPORTE-N2", despesa(categoria="representacao", valor=190))
        self.assertEqual(b.motivo, "categoria_nao_coberta")

    def test_amb_027_sem_arquivo_vale_a_padrao_igual_a_v3(self):
        a, = avaliar("CC-COMERCIAL", despesa(valor=90), politica=POLITICA_PADRAO)
        self.assertEqual((a.reembolsavel, a.status), (6000, "parcial"))


if __name__ == "__main__":
    unittest.main()
