"""T-015: ponta a ponta com os arquivos do envelope contra E-02 e E-03 da spec."""
import json, os, tempfile, unittest
import apoio  # noqa: F401
from reembolso.cli import main

ENV = os.path.join(os.path.dirname(__file__), "..", "exemplos", "envelope")
ARGS = ["--politica", os.path.join(ENV, "politica-v4.json"), "--cambio", os.path.join(ENV, "cambio.json")]

E_02 = {  # id: (moeda, taxa, solicitado, reembolsável, status, motivo)
    "e-001": ("BRL", 1, 340.00, 300.00, "parcial", "acima_do_limite_diario"),
    "e-002": ("EUR", 5.93, 130.46, 90.00, "parcial", "acima_do_limite_diario"),
    "e-003": ("EUR", 5.88, 85.26, 85.26, "aprovado", "dentro_do_limite"),
    "e-004": ("EUR", 5.96, 178.80, 90.00, "parcial", "acima_do_limite_diario"),
    "e-005": ("USD", 5.50, 220.00, 0.00, "recusado", "sem_nota_fiscal"),
    "e-006": ("GBP", None, None, 0.00, "recusado", "cambio_indisponivel"),
    "e-007": ("BRL", 1, 1200.00, 600.00, "pendente", "acima_do_limite_diario"),
    "e-008": ("BRL", 1, 95.00, 95.00, "aprovado", "dentro_do_limite"),
    "e-009": ("BRL", 1, 120.00, 0.00, "recusado", "categoria_nao_coberta"),
    "e-010": ("BRL", 1, 88.00, 88.00, "aprovado", "dentro_do_limite"),
}
E_03 = {
    "f-001": ("BRL", 1, 58.00, 58.00, "aprovado", "dentro_do_limite"),
    "f-002": ("BRL", 1, 310.00, 310.00, "aprovado", "dentro_do_limite"),
    "f-003": ("BRL", 1, 190.00, 0.00, "recusado", "categoria_nao_coberta"),
    "f-004": ("USD", 5.48, 65.76, 65.76, "aprovado", "dentro_do_limite"),
}


def rodar(arquivo):
    saida = os.path.join(tempfile.mkdtemp(), "r.json")
    assert main(["calcular", "--input", os.path.join(ENV, arquivo), "--output", saida] + ARGS) == 0
    out = json.load(open(saida))
    return out, {i["id"]: (i["moeda"], i["taxa_cambio"], i["valor_solicitado"], i["valor_reembolsavel"],
                           i["status"], i["motivo"]) for i in out["itens"]}


class TestEnvelope(unittest.TestCase):
    def test_e_02_envelope_comercial_bate_com_a_spec(self):
        out, itens = rodar("despesas-envelope.json")
        self.assertEqual(itens, E_02)
        self.assertEqual(out["politica"], "v4")
        self.assertEqual(out["resumo"], {"total_solicitado": 2457.52, "total_reembolsavel": 748.26,
                                         "total_pendente": 600.0, "aprovados": 3, "parciais": 3,
                                         "recusados": 3, "pendentes": 1})

    def test_e_03_envelope_cc_desconhecido_bate_com_a_spec(self):
        out, itens = rodar("despesas-envelope-cc-desconhecido.json")
        self.assertEqual(itens, E_03)
        self.assertEqual(out["resumo"], {"total_solicitado": 623.76, "total_reembolsavel": 433.76,
                                         "total_pendente": 0.0, "aprovados": 3, "parciais": 0,
                                         "recusados": 1, "pendentes": 0})

    def test_cli_politica_invalida_sai_com_2(self):
        saida = os.path.join(tempfile.mkdtemp(), "r.json")
        self.assertEqual(main(["calcular", "--input", os.path.join(ENV, "despesas-envelope.json"),
                               "--output", saida, "--politica", os.path.join(ENV, "cambio.json")]), 2)
        self.assertFalse(os.path.exists(saida))


if __name__ == "__main__":
    unittest.main()
