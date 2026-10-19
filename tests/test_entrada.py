import unittest
from apoio import pedido, despesa
from reembolso.entrada import EntradaInvalida, centavos


class TestEntrada(unittest.TestCase):
    def test_rn_010_valor_arredonda_meio_para_cima(self):
        self.assertEqual(centavos(33.333), 3333)
        self.assertEqual(centavos(33.335), 3334)
        self.assertEqual(centavos(72.50), 7250)

    def test_b_09_meio_centavo_arredonda_para_cima(self):
        self.assertEqual(centavos(0.005), 1)

    def test_b_14_nota_ausente_e_false(self):
        d = despesa(); del d["tem_nota_fiscal"]
        self.assertFalse(pedido(d).despesas[0].tem_nota_fiscal)

    def test_b_15_campo_obrigatorio_ausente_levanta_erro(self):
        d = despesa(); del d["valor"]
        with self.assertRaises(EntradaInvalida):
            pedido(d)
        with self.assertRaises(EntradaInvalida):
            pedido(despesa(data="ontem"))
        with self.assertRaises(EntradaInvalida):
            pedido(despesa(valor="abc"))

    def test_rn_010_categoria_e_fornecedor_normalizados(self):
        p = pedido(despesa(categoria=" ALIMENTACAO ", fornecedor=" Bistro "))
        self.assertEqual(p.despesas[0].categoria, "alimentacao")
        self.assertEqual(p.despesas[0].fornecedor, " Bistro ")
        self.assertEqual(p.despesas[0].fornecedor_norm, "bistro")


if __name__ == "__main__":
    unittest.main()
