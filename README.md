# Motor de Cálculo de Reembolso

CLI que lê um JSON de despesas de um colaborador e devolve, item a item, quanto
é reembolsável e por quê, segundo a política de reembolso do RH desambiguada em
[`specs/001-motor-reembolso/spec.md`](specs/001-motor-reembolso/spec.md).

Desafio prático de Spec Driven Development da Anthropic Academy. O enunciado
original está em [`DESAFIO.md`](DESAFIO.md).

## Requisitos

Python 3.10 ou mais novo. Nenhuma dependência além da biblioteca padrão.

## Como rodar

```bash
./reembolso calcular --input exemplos/despesas-exemplo.json --output resultado.json
```

Equivalente sem o atalho:

```bash
PYTHONPATH=src python3 -m reembolso calcular --input exemplos/despesas-exemplo.json --output resultado.json
```

Com a política v4 do Dia 2 (limites por centro de custo) e a tabela de câmbio:

```bash
./reembolso calcular --input exemplos/envelope/despesas-envelope.json --output resultado.json --politica exemplos/envelope/politica-v4.json --cambio exemplos/envelope/cambio.json
```

`--politica` e `--cambio` são opcionais. Sem `--politica` vale a política
padrão embutida (igual à v3). Sem `--cambio` só despesas em BRL são aceitas.

Saída: um JSON com `itens[]` (um por despesa, com `valor_reembolsavel`,
`status` e `motivo`) e um `resumo`. O schema completo está na seção 4.2 da
spec. Entrada malformada termina com código 2, mensagem em stderr e nenhum
arquivo de saída.

## Como testar

```bash
python3 -m unittest discover -s tests -v
```

Os nomes dos testes citam a regra da spec que verificam (`test_rn_003_...`,
`test_b_10_...`). O teste `test_e_01_exemplo_oficial_bate_com_a_spec` roda a
CLI sobre `exemplos/despesas-exemplo.json` e compara com a tabela E-01 da spec;
`test_e_02_*` e `test_e_03_*` fazem o mesmo com os arquivos do envelope.

## Estrutura

```
specs/001-motor-reembolso/   spec.md (o quê), plan.md (como), tasks.md (ordem), DECISIONS.md (mudanças)
src/reembolso/               entrada.py, politica.py, cambio.py, motor.py, saida.py, cli.py
tests/                       unittest, um arquivo por fatia
docs/sessions/               sessões do Claude Code exportadas
docs/RELATORIO.md            relatório final
exemplos/                    entrada de referência e arquivos do envelope do Dia 2
```
