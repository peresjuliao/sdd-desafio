import json, os, subprocess, sys, tempfile, unittest
import apoio  # noqa: F401  (ajusta sys.path)
from reembolso.cli import main

RAIZ = os.path.join(os.path.dirname(__file__), "..")


class TestCli(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.entrada = os.path.join(self.dir, "in.json")
        self.saida = os.path.join(self.dir, "out.json")

    def _escreve(self, dados):
        with open(self.entrada, "w") as f:
            json.dump(dados, f)

    def test_cli_escreve_saida_no_schema(self):
        self._escreve({"colaborador": {"id": "c-1"}, "periodo": {"inicio": "2026-07-01", "fim": "2026-07-31"},
                       "despesas": [{"id": "d-1", "data": "2026-07-03", "categoria": "alimentacao",
                                     "valor": 72.5, "tem_nota_fiscal": True}]})
        self.assertEqual(main(["calcular", "--input", self.entrada, "--output", self.saida]), 0)
        out = json.load(open(self.saida))
        self.assertEqual(out["politica"], "v3")
        item = out["itens"][0]
        self.assertEqual(item["valor_solicitado"], 72.5)
        self.assertEqual(item["valor_reembolsavel"], 60.0)
        self.assertEqual(item["status"], "parcial")
        self.assertEqual(item["motivo"], "acima_do_limite_diario")
        self.assertIn("60,00", item["detalhe"])
        self.assertEqual(out["resumo"], {"total_solicitado": 72.5, "total_reembolsavel": 60.0, "total_pendente": 0.0,
                                         "aprovados": 0, "parciais": 1, "recusados": 0, "pendentes": 0})

    def test_cli_entrada_invalida_nao_escreve_saida(self):
        self._escreve({"colaborador": {"id": "c-1"}, "periodo": {"inicio": "2026-07-01"}, "despesas": []})
        self.assertEqual(main(["calcular", "--input", self.entrada, "--output", self.saida]), 2)
        self.assertFalse(os.path.exists(self.saida))

    def test_cli_script_na_raiz_roda(self):
        self._escreve({"colaborador": {"id": "c-1"}, "periodo": {"inicio": "2026-07-01", "fim": "2026-07-31"},
                       "despesas": []})
        r = subprocess.run([os.path.join(RAIZ, "reembolso"), "calcular", "--input", self.entrada,
                            "--output", self.saida], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.load(open(self.saida))["itens"], [])


if __name__ == "__main__":
    unittest.main()
