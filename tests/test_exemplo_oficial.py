"""T-011: ponta a ponta com exemplos/despesas-exemplo.json contra a tabela E-01 da spec."""
import json, os, tempfile, unittest
import apoio  # noqa: F401
from reembolso.cli import main

EXEMPLO = os.path.join(os.path.dirname(__file__), "..", "exemplos", "despesas-exemplo.json")

E_01 = {  # id: (reembolsável, status, motivo) — copiado da spec seção 7
    "d-001": (60.00, "parcial", "acima_do_limite_diario"),
    "d-002": (0.00, "recusado", "acima_do_limite_diario"),
    "d-003": (80.00, "parcial", "acima_do_limite_diario"),
    "d-004": (0.00, "recusado", "sem_nota_fiscal"),
    "d-005": (0.00, "recusado", "categoria_nao_coberta"),
    "d-006": (54.90, "aprovado", "dentro_do_limite"),
    "d-007": (0.00, "recusado", "duplicata"),
    "d-008": (0.00, "recusado", "fora_da_competencia"),
    "d-009": (0.00, "recusado", "valor_invalido"),
    "d-010": (375.00, "parcial", "acima_do_limite_diario"),
    "d-011": (33.33, "aprovado", "dentro_do_limite"),
    "d-012": (47.20, "aprovado", "dentro_do_limite"),
    "d-013": (0.00, "recusado", "sem_nota_fiscal"),
    "d-014": (60.00, "parcial", "acima_do_limite_diario"),
}


class TestExemploOficial(unittest.TestCase):
    def test_e_01_exemplo_oficial_bate_com_a_spec(self):
        saida = os.path.join(tempfile.mkdtemp(), "resultado.json")
        self.assertEqual(main(["calcular", "--input", EXEMPLO, "--output", saida]), 0)
        out = json.load(open(saida))
        obtido = {i["id"]: (i["valor_reembolsavel"], i["status"], i["motivo"]) for i in out["itens"]}
        self.assertEqual(obtido, E_01)
        self.assertEqual([i["id"] for i in out["itens"]], list(E_01))
        self.assertEqual(out["resumo"], {"total_solicitado": 1816.84, "total_reembolsavel": 710.43,
                                         "aprovados": 3, "parciais": 4, "recusados": 7})

    def test_saida_e_deterministica(self):
        a = os.path.join(tempfile.mkdtemp(), "a.json"); b = os.path.join(tempfile.mkdtemp(), "b.json")
        main(["calcular", "--input", EXEMPLO, "--output", a]); main(["calcular", "--input", EXEMPLO, "--output", b])
        self.assertEqual(open(a).read(), open(b).read())


if __name__ == "__main__":
    unittest.main()
