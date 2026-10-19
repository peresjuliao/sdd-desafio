"""T-013: moeda e conversão (RN-014)."""
import os, unittest
from decimal import Decimal
from apoio import pedido, despesa
from reembolso.cambio import carregar_cambio, taxa_para, converter, SEM_CAMBIO
from reembolso.motor import calcular
from reembolso.politica import POLITICA_PADRAO

CAMBIO = carregar_cambio(os.path.join(os.path.dirname(__file__), "..", "exemplos", "envelope", "cambio.json"))


def avaliar(*despesas, cambio=CAMBIO):
    return calcular(pedido(*despesas), POLITICA_PADRAO, cambio).avaliacoes


class TestCambio(unittest.TestCase):
    def test_rn_014_converte_pela_taxa_da_data(self):
        a, = avaliar(despesa(data="2026-07-14", valor=22, moeda="EUR"))
        self.assertEqual((a.valor_brl, a.taxa), (13046, Decimal("5.93")))
        self.assertEqual((a.reembolsavel, a.status), (6000, "parcial"))

    def test_rn_014_brl_tem_taxa_1_e_e_o_padrao(self):
        a, = avaliar(despesa(valor=10), cambio=SEM_CAMBIO)
        self.assertEqual((a.valor_brl, a.taxa, a.despesa.moeda), (1000, 1, "BRL"))

    def test_rn_014_sem_taxa_na_data_usa_anterior_mais_recente(self):
        a, = avaliar(despesa(data="2026-07-18", valor=30, moeda="EUR"))   # sábado → 17/07
        self.assertEqual((a.valor_brl, a.taxa), (17880, Decimal("5.96")))

    def test_rn_014_moeda_sem_taxa_e_cambio_indisponivel(self):
        a, = avaliar(despesa(data="2026-07-21", valor=55, moeda="GBP"))
        self.assertEqual((a.status, a.motivo, a.valor_brl, a.taxa), ("recusado", "cambio_indisponivel", None, None))

    def test_b_20_data_anterior_a_primeira_taxa(self):
        a, = avaliar(despesa(data="2026-07-10", valor=10, moeda="EUR"))
        self.assertEqual(a.motivo, "cambio_indisponivel")

    def test_b_22_sem_arquivo_de_cambio_usd_e_indisponivel(self):
        a, = avaliar(despesa(valor=10, moeda="USD"), cambio=SEM_CAMBIO)
        self.assertEqual(a.motivo, "cambio_indisponivel")

    def test_b_19_moeda_minuscula_e_normalizada(self):
        a, = avaliar(despesa(data="2026-07-14", valor=1, moeda=" eur "))
        self.assertEqual((a.despesa.moeda, a.valor_brl), ("EUR", 593))

    def test_amb_021_arredonda_uma_vez_meio_para_cima(self):
        self.assertEqual(converter(1450, Decimal("5.88")), 8526)
        self.assertEqual(converter(1, Decimal("5.445")), 5)   # 5,445 → 5
        self.assertEqual(converter(1, Decimal("5.45")), 5)    # 5,45 → 5
        self.assertEqual(converter(1, Decimal("5.5")), 6)     # 5,5 → 6

    def test_amb_022_piso_de_nota_sobre_valor_em_reais(self):
        a, = avaliar(despesa(data="2026-07-20", categoria="transporte_urbano", valor=40, moeda="USD",
                             tem_nota_fiscal=False))   # 40 USD = 220,00
        self.assertEqual(a.motivo, "sem_nota_fiscal")

    def test_b_23_moedas_diferentes_nao_sao_duplicata(self):
        a, b = avaliar(despesa(data="2026-07-14", valor=22, moeda="EUR"),
                       despesa(data="2026-07-14", valor=130.46))
        self.assertNotEqual(b.motivo, "duplicata")

    def test_rn_009_valor_negativo_em_moeda_estrangeira_e_invalido(self):
        a, = avaliar(despesa(data="2026-07-14", valor=-5, moeda="EUR"))
        self.assertEqual(a.motivo, "valor_invalido")

    def test_rn_012_total_solicitado_ignora_item_sem_conversao(self):
        r = calcular(pedido(despesa(valor=10), despesa(valor=5, moeda="GBP", fornecedor="G")), POLITICA_PADRAO, CAMBIO)
        self.assertEqual(r.resumo["total_solicitado"], 1000)

    def test_taxa_para_ordem_das_datas_nao_importa_no_arquivo(self):
        c = {"taxas": dict(sorted({__import__("datetime").date(2026, 7, 1): {"USD": Decimal(5)},
                                   __import__("datetime").date(2026, 7, 3): {"USD": Decimal(6)}}.items()))}
        self.assertEqual(taxa_para(c, "USD", __import__("datetime").date(2026, 7, 2)), 5)
        self.assertEqual(taxa_para(c, "USD", __import__("datetime").date(2026, 7, 3)), 6)


if __name__ == "__main__":
    unittest.main()
