# CLAUDE.md

## O projeto

Motor de cálculo de reembolso de despesas corporativas. CLI que lê um JSON de
despesas e emite um JSON com o valor reembolsável e a justificativa de cada item.

## Fonte da verdade

`specs/001-motor-reembolso/spec.md` define **o que** o sistema faz.
`specs/001-motor-reembolso/plan.md` define **como**.
`specs/001-motor-reembolso/tasks.md` define **em que ordem**.

Quando o código e a spec discordarem, a spec está certa e o código é o bug —
a menos que a spec esteja errada, e nesse caso corrigimos a spec primeiro e
registramos em `DECISIONS.md`.

**Antes de implementar qualquer coisa, leia a task correspondente em `tasks.md`.**
Se o que eu pedi não está coberto por nenhuma task, me avise em vez de implementar.

## Regras de trabalho

- Toda regra de negócio vive na spec, não no chat e não em comentário de código.
- Se eu te explicar uma regra que não está na spec, **pare e me diga isso** antes
  de escrever código. Isso é um bug de spec.
- Todo commit referencia uma task: `feat(T-003): <descrição>`.
  Mudanças de documentação: `docs(spec):`, `docs(plan):`, `docs(tasks):`.
- Nenhuma regra de negócio entra sem teste.
- Ao marcar uma task como feita em `tasks.md`, preencher o hash do commit.
- Ao fim de cada sessão, lembrar o usuário de rodar `/export` para
  `docs/sessions/NN-descricao-curta.md` e commitar.

## Stack e comandos

- Linguagem: Python 3.12, só biblioteca padrão. Nenhuma dependência.
- Rodar: `./reembolso calcular --input exemplos/despesas-exemplo.json --output resultado.json`
  (opcionais: `--politica exemplos/envelope/politica-v4.json --cambio exemplos/envelope/cambio.json`)
- Testes: `python3 -m unittest discover -s tests -v`
- Lint/format: nenhum.

## Convenções de código

- Código em `src/reembolso/`, um módulo por peça do `plan.md` seção 2.
- Testes em `tests/`, nome `test_rn_NNN_<frase do aceite>` ou `test_b_NN_<frase>`.
- Valores monetários: inteiros em centavos em todo o motor; conversão de/para
  reais só em `entrada.py` e `saida.py`; câmbio com `Decimal` em `cambio.py`.
- Erro de entrada: `EntradaInvalida`, capturada só na CLI (código de saída 2).
- Sem classes além de dataclasses; sem abstração com uma implementação só.

## Fora de escopo

- Ver `spec.md` seção 3. Em especial: não interpretar `descricao`, não tratar
  não buscar cotação fora da tabela fornecida, não inventar regra de fim de semana.
