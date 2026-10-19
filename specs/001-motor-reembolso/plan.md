# Plano Técnico — Motor de Cálculo de Reembolso

**Versão:** 1.0 · **Baseado na spec:** 1.0

> Aqui mora o COMO. Nenhuma regra de negócio nova: se apareceu uma, ela
> pertence à `spec.md`.

---

## 1. Stack

| Escolha | O quê | Por quê | O que descartei e por quê |
|---|---|---|---|
| Linguagem | Python 3.12, só biblioteca padrão | já instalado na máquina; o problema é dicionários, datas e inteiros | Node/Go: nada a ganhar, mais setup |
| Testes | `unittest` (stdlib), `python -m unittest discover tests` | zero dependência; `pytest` não está instalado e instalar não compra nada aqui | pytest: dependência para um projeto de dois dias |
| Parsing/validação | `json` + `argparse` + `datetime.date.fromisoformat`; validação manual dos campos obrigatórios com mensagens claras | entrada pequena e com schema fixo | pydantic/jsonschema: dependência para validar 13 campos |
| Aritmética monetária | inteiros em centavos; conversão na leitura com `Decimal(str(valor)).quantize(0.01, ROUND_HALF_UP)` | 33.333 e 0.1+0.2 não existem em centavos inteiros | `float` em todo lugar: a fonte de bug mais previsível do projeto |

## 2. Arquitetura

```
despesas.json → leitura/validação → normalização → motor (regras da spec, ordem da seção 8) → serialização → resultado.json
```

Peças (um módulo cada, dentro de `src/reembolso/`):

- `entrada.py` — lê o JSON, valida obrigatórios, converte `valor` para centavos
  e `data` para `date`. Única peça que conhece o formato de entrada.
- `politica.py` — a tabela de limites (RN-001), o piso de nota (RN-003) e o
  percentual de viagem (RN-004), como dados, não como `if`s espalhados.
- `motor.py` — função pura `calcular(pedido, politica) -> resultado`. Sem I/O.
  Implementa a ordem da seção 8 da spec.
- `saida.py` — transforma o resultado em dicionários com valores em reais
  (2 casas) e escreve o JSON.
- `cli.py` — `argparse`, subcomando `calcular --input --output`.

**Fronteiras:** `motor.py` recebe estruturas já validadas e uma política; não
lê arquivo, não formata dinheiro, não conhece `argparse`. Tudo que é regra de
negócio está ali e só ali. Mudança de formato de entrada toca `entrada.py`;
mudança de valor de limite toca `politica.py`; mudança de regra toca
`motor.py` e a spec.

## 3. Modelo de dados

- `Despesa` (dataclass, imutável): `id`, `data: date`, `categoria: str` (já
  normalizada), `descricao`, `fornecedor` (normalizado para comparação, original
  guardado para saída), `valor: int` (centavos), `tem_nota_fiscal: bool`.
- `Pedido`: `colaborador: dict`, `periodo` (`inicio`, `fim` como `date`,
  demais campos copiados), `despesas: list[Despesa]`.
- `Avaliacao`: `despesa`, `reembolsavel: int` (centavos), `status`, `motivo`,
  `detalhe`.
- `Resultado`: `avaliacoes: list[Avaliacao]` + resumo derivado.

A justificativa (`detalhe`) é montada no motor no momento da decisão, com os
números que a produziram, para que a saída seja auditável sem rerodar.

## 4. Como a política é representada

Um dicionário em `politica.py`:

```python
POLITICA_V3 = {
    "versao": "v3",
    "limites": {"alimentacao": 6000, "transporte_urbano": 8000, "hospedagem": 25000},
    "nota_fiscal_obrigatoria_acima_de": 10000,
    "acrescimo_em_viagem_percentual": 50,
}
```

O motor recebe a política como argumento. Hoje há uma só, constante no código.
Se a política passar a vir de fora, troca-se a origem do dicionário sem tocar
o motor. Não vou além disso: carregar arquivo de política sem requisito é
arquitetura genérica no lugar errado.

## 5. Decisões técnicas

### DT-001 — Centavos inteiros, conversão só nas bordas

**Contexto:** a entrada tem 33.333 e a política tem limites com centavos.
**Decisão:** `entrada.py` converte para `int` centavos com `Decimal` e
`ROUND_HALF_UP`; `saida.py` divide por 100 só na hora de escrever.
**Alternativa descartada:** `Decimal` em todo o motor — funciona, mas é mais
verboso que `int` e não compra nada depois da conversão.
**Consequência:** comparações e somas exatas; testes escrevem valores como
`6000` e ficam feios de ler, mitigado com um helper `reais("60.00")`.

### DT-002 — Motor como função pura, uma passada por item

**Contexto:** a spec define ordem de regras e "primeira que recusa vence".
**Decisão:** `calcular` pré-computa duas coisas (dias em viagem, chaves de
duplicata já vistas) e depois percorre os itens uma vez, aplicando a seção 8
como uma sequência de `if`s que retornam cedo. O saldo da cota diária é um
`dict[(data, categoria)] -> int` mutado durante a passada.
**Alternativa descartada:** pipeline de "regras" como objetos/plugins —
abstração para 7 regras que nunca serão combinadas de outro jeito.
**Consequência:** o motor cabe numa tela; para adicionar regra se edita uma
função. Se a ordem mudar, edita-se a mesma função e a spec.

### DT-003 — Sem dependências, sem empacotamento

**Contexto:** entrega é um fork que o avaliador clona e roda.
**Decisão:** `python -m reembolso calcular ...` com `PYTHONPATH=src`, ou o
script `reembolso` na raiz que faz isso. Nada de `pip install`.
**Alternativa descartada:** `pyproject.toml` + `pip install -e .` — um passo a
mais para falhar na máquina do avaliador.
**Consequência:** sem versão, sem publicação; aceitável para o escopo.

### DT-004 — Erro de entrada é exceção própria, capturada só na CLI

**Contexto:** spec 4.1 exige erro descritivo e nenhuma saída.
**Decisão:** `EntradaInvalida(Exception)` lançada por `entrada.py`; `cli.py`
captura, imprime em stderr e sai com código 2. O arquivo de saída só é aberto
depois do cálculo terminar.
**Alternativa descartada:** validar e escrever saída parcial com erros dentro —
mistura dois contratos.

## 6. Estratégia de testes

- **Nível:** unitários sobre `calcular` (a maioria) + um ponta a ponta pela
  CLI com `exemplos/despesas-exemplo.json` comparado à tabela E-01.
- **Cada RN tem teste?** sim: um método `test_rn_0NN_...` por regra em
  `tests/test_regras.py`; casos de borda `test_b_NN_...` em
  `tests/test_bordas.py`; a matriz de cobertura em `tasks.md` lista o nome.
- **Nomenclatura:** `test_rn_003_cem_reais_exatos_nao_exige_nota`. O id da
  spec vem no nome, o resto é a frase do aceite.
- **Construção de casos:** helper `despesa(**kw)` com defaults válidos, para
  que cada teste mostre só o que importa.

## 7. Riscos

| Risco | Probabilidade | O que faço se acontecer |
|---|---|---|
| Float na leitura (`json` entrega `float`) estragar centavos | alta se esquecer | `Decimal(str(x))`, nunca `Decimal(x)`; teste B-09 cobre |
| Conjunto oculto do avaliador com campo opcional ausente | média | defaults declarados na spec 4.1; teste B-14 |
| Mudança do Dia 2 exigir política de fora | desconhecida | política já é um dicionário injetado no motor; troca-se a origem |
| Mudança do Dia 2 mexer na ordem das regras | desconhecida | a ordem está numa única função; atualizar spec seção 8 antes |
