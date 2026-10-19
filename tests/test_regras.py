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


if __name__ == "__main__":
    unittest.main()
