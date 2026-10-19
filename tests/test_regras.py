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


class TestCategoria(unittest.TestCase):
    def test_rn_008_categoria_fora_da_politica_recusada(self):
        a, = avaliar(despesa(categoria="coworking", valor=89))
        self.assertEqual((a.status, a.motivo, a.reembolsavel), ("recusado", "categoria_nao_coberta", 0))

    def test_rn_010_categoria_maiuscula_e_normalizada(self):
        a, = avaliar(despesa(categoria="ALIMENTACAO", valor=10))
        self.assertEqual(a.status, "aprovado")
        self.assertEqual(a.despesa.categoria, "alimentacao")


class TestValor(unittest.TestCase):
    def test_rn_009_estorno_negativo_recusado_e_nao_abate(self):
        corrida, estorno = avaliar(despesa(categoria="transporte_urbano", valor=30),
                                   despesa(categoria="transporte_urbano", valor=-45))
        self.assertEqual((estorno.status, estorno.motivo, estorno.reembolsavel), ("recusado", "valor_invalido", 0))
        self.assertEqual(corrida.reembolsavel, 3000)

    def test_b_08_valor_zero_invalido(self):
        a, = avaliar(despesa(valor=0))
        self.assertEqual(a.motivo, "valor_invalido")


class TestCompetencia(unittest.TestCase):
    def test_rn_006_fora_da_competencia_recusado(self):
        a, = avaliar(despesa(data="2026-04-15"))
        self.assertEqual((a.status, a.motivo), ("recusado", "fora_da_competencia"))

    def test_b_06_pontas_do_periodo_aceitas(self):
        a, b = avaliar(despesa(data="2026-07-01"), despesa(data="2026-07-31"))
        self.assertEqual((a.status, b.status), ("aprovado", "aprovado"))

    def test_b_07_dia_antes_do_inicio_recusado(self):
        a, b = avaliar(despesa(data="2026-06-30"), despesa(data="2026-08-01"))
        self.assertEqual((a.motivo, b.motivo), ("fora_da_competencia", "fora_da_competencia"))


class TestDuplicata(unittest.TestCase):
    def test_rn_007_segunda_ocorrencia_e_duplicata(self):
        a, b = avaliar(despesa(id="d-006", data="2026-07-09", fornecedor="Bistro Central", valor=54.90),
                       despesa(id="d-007", data="2026-07-09", fornecedor="Bistro Central", valor=54.90))
        self.assertEqual((a.status, a.reembolsavel), ("aprovado", 5490))
        self.assertEqual((b.status, b.motivo, b.reembolsavel), ("recusado", "duplicata", 0))

    def test_b_11_descricao_diferente_ainda_e_duplicata(self):
        a, b = avaliar(despesa(descricao="Almoco", fornecedor="bistro central"),
                       despesa(descricao="Jantar", fornecedor=" Bistro Central "))
        self.assertEqual(b.motivo, "duplicata")

    def test_b_12_tres_iguais_recusa_duas(self):
        a, b, c = avaliar(despesa(), despesa(), despesa())
        self.assertEqual([x.motivo for x in (a, b, c)], ["dentro_do_limite", "duplicata", "duplicata"])

    def test_rn_007_data_diferente_nao_e_duplicata(self):
        a, b = avaliar(despesa(data="2026-07-09"), despesa(data="2026-07-10"))
        self.assertEqual(b.status, "aprovado")


class TestNotaFiscal(unittest.TestCase):
    def test_rn_003_cem_reais_exatos_nao_exige_nota(self):
        a, = avaliar(despesa(categoria="transporte_urbano", valor=100.00, tem_nota_fiscal=False))
        self.assertNotEqual(a.motivo, "sem_nota_fiscal")

    def test_rn_003_cem_e_um_centavo_sem_nota_recusado(self):
        a, = avaliar(despesa(categoria="transporte_urbano", valor=100.01, tem_nota_fiscal=False))
        self.assertEqual((a.status, a.motivo, a.reembolsavel), ("recusado", "sem_nota_fiscal", 0))

    def test_rn_003_acima_de_cem_com_nota_passa(self):
        a, = avaliar(despesa(categoria="hospedagem", valor=200, tem_nota_fiscal=True))
        self.assertEqual(a.status, "aprovado")

    def test_amb_012_piso_e_por_item_nao_por_dia(self):
        a, b = avaliar(despesa(categoria="transporte_urbano", valor=60, tem_nota_fiscal=False),
                       despesa(categoria="transporte_urbano", valor=60, tem_nota_fiscal=False, fornecedor="G"))
        self.assertNotEqual(a.motivo, "sem_nota_fiscal")
        self.assertNotEqual(b.motivo, "sem_nota_fiscal")


class TestCotaDiaria(unittest.TestCase):
    def test_rn_001_dois_almocos_somam_na_cota_do_dia(self):
        a, b = avaliar(despesa(valor=72.50), despesa(valor=38.00, fornecedor="G"))
        self.assertEqual(a.reembolsavel + b.reembolsavel, 6000)
        c, = avaliar(despesa(valor=54.90))
        self.assertEqual((c.reembolsavel, c.status), (5490, "aprovado"))

    def test_rn_002_excedente_e_cortado_e_segundo_item_zera(self):
        a, b = avaliar(despesa(valor=72.50), despesa(valor=38.00, fornecedor="G"))
        self.assertEqual((a.reembolsavel, a.status, a.motivo), (6000, "parcial", "acima_do_limite_diario"))
        self.assertEqual((b.reembolsavel, b.status, b.motivo), (0, "recusado", "acima_do_limite_diario"))

    def test_b_01_exatamente_no_limite_aprovado(self):
        a, = avaliar(despesa(valor=60.00))
        self.assertEqual((a.reembolsavel, a.status), (6000, "aprovado"))

    def test_b_02_um_centavo_acima_e_parcial(self):
        a, = avaliar(despesa(valor=60.01))
        self.assertEqual((a.reembolsavel, a.status), (6000, "parcial"))

    def test_b_05_item_sem_nota_nao_consome_cota(self):
        a, b = avaliar(despesa(categoria="transporte_urbano", valor=100.01, tem_nota_fiscal=False),
                       despesa(categoria="transporte_urbano", valor=50, fornecedor="G"))
        self.assertEqual(a.motivo, "sem_nota_fiscal")
        self.assertEqual((b.reembolsavel, b.status), (5000, "aprovado"))

    def test_rn_001_categorias_tem_cotas_separadas_no_mesmo_dia(self):
        a, b = avaliar(despesa(valor=60), despesa(categoria="transporte_urbano", valor=80))
        self.assertEqual((a.status, b.status), ("aprovado", "aprovado"))

    def test_amb_003_cota_e_consumida_na_ordem_da_entrada(self):
        a, b = avaliar(despesa(valor=38.00), despesa(valor=72.50, fornecedor="G"))
        self.assertEqual((a.reembolsavel, b.reembolsavel), (3800, 2200))


if __name__ == "__main__":
    unittest.main()
