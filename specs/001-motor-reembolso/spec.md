# Spec — Motor de Cálculo de Reembolso

**Versão:** 1.1 · **Status:** aprovada para implementação · **Última alteração:** 2026-10-19

> Este arquivo descreve o QUÊ e o PORQUÊ. Nenhuma linha aqui cita linguagem,
> biblioteca, classe, função ou estrutura de pasta. Solução mora no `plan.md`.
>
> Teste de aceitação da própria spec: uma pessoa que nunca viu o projeto
> consegue, lendo só este arquivo, verificar se o sistema está correto?

---

## 1. Problema

O financeiro confere na mão, item por item, as despesas de cada colaborador
contra a Política de Reembolso v3 do RH. A política é curta e ambígua, então
duas pessoas chegam a resultados diferentes para a mesma planilha, e ninguém
registra por que um item foi cortado.

## 2. Objetivo

Dado o conjunto de despesas de um colaborador num período, o sistema devolve,
para cada despesa, quanto é reembolsável e o motivo, de forma determinística e
auditável.

## 3. Fora de escopo

- Não lê planilhas, e-mail ou qualquer formato além do JSON de entrada definido.
- Não consulta o RH, o financeiro ou qualquer sistema externo.
- Não interpreta o texto livre de `descricao` (ex.: "2 diárias", "estorno").
- Não trata moeda estrangeira: todo valor é tratado como real brasileiro.
- Não diferencia dia útil, fim de semana, feriado ou plantão (AMB-011).
- Não compensa créditos ou estornos contra despesas (AMB-008).
- Não aprova nem paga: produz um parecer; a decisão final continua humana.
- Não guarda estado entre execuções: cada arquivo de entrada é avaliado sozinho.

## 4. Entrada e saída

### 4.1 Entrada

Conforme `exemplos/despesas-exemplo.json`.

| Campo | Tipo | Significado | Obrigatório |
|---|---|---|---|
| `colaborador.id` | texto | identificador do colaborador | sim |
| `colaborador.nome` | texto | nome; copiado para a saída | não |
| `colaborador.centro_custo` | texto | centro de custo; copiado para a saída, sem efeito no cálculo nesta versão | não |
| `periodo.competencia` | texto `AAAA-MM` | rótulo do período; copiado para a saída | não |
| `periodo.inicio` | data `AAAA-MM-DD` | primeiro dia aceito (inclusive) | sim |
| `periodo.fim` | data `AAAA-MM-DD` | último dia aceito (inclusive) | sim |
| `despesas[].id` | texto | identificador único do item na saída | sim |
| `despesas[].data` | data `AAAA-MM-DD` | data em que a despesa ocorreu | sim |
| `despesas[].categoria` | texto | categoria; comparação sem distinção de maiúsculas e espaços nas pontas (AMB-009) | sim |
| `despesas[].descricao` | texto | texto livre; copiado para a saída, nunca interpretado | não |
| `despesas[].fornecedor` | texto | quem recebeu; usado na detecção de duplicata | não (ausente = vazio) |
| `despesas[].valor` | número | valor em reais; arredondado a centavos na leitura (AMB-008) | sim |
| `despesas[].tem_nota_fiscal` | booleano | se há nota fiscal | não (ausente = `false`) |

Entrada malformada (JSON inválido, campo obrigatório ausente, data ilegível,
valor não numérico) encerra a execução com erro descritivo e nenhum arquivo de
saída é escrito.

### 4.2 Saída

| Campo | Tipo | Significado |
|---|---|---|
| `politica` | texto | versão da política aplicada (`"v3"`) |
| `colaborador` | objeto | cópia do bloco de entrada |
| `periodo` | objeto | cópia do bloco de entrada |
| `itens[]` | lista | um item por despesa de entrada, na mesma ordem |
| `itens[].id` | texto | id da despesa |
| `itens[].data` | data | data da despesa |
| `itens[].categoria` | texto | categoria normalizada (minúsculas) |
| `itens[].descricao` | texto | cópia |
| `itens[].valor_solicitado` | número (2 casas) | valor da despesa após arredondamento |
| `itens[].valor_reembolsavel` | número (2 casas) | quanto a empresa paga por este item |
| `itens[].status` | texto | `aprovado` (paga tudo), `parcial` (paga parte), `recusado` (paga zero) |
| `itens[].motivo` | texto | código do motivo (tabela abaixo) |
| `itens[].detalhe` | texto | frase legível explicando o motivo, com os números usados |
| `resumo.total_solicitado` | número | soma de `valor_solicitado` de todos os itens |
| `resumo.total_reembolsavel` | número | soma de `valor_reembolsavel` |
| `resumo.aprovados` / `parciais` / `recusados` | inteiro | contagem por status |

Códigos de `motivo`:

| Código | Quando | Status resultante |
|---|---|---|
| `dentro_do_limite` | item cabe inteiro na cota do dia | `aprovado` |
| `acima_do_limite_diario` | cota do dia cobre parte ou nada do item | `parcial` ou `recusado` |
| `sem_nota_fiscal` | valor acima do piso de nota e `tem_nota_fiscal` falso | `recusado` |
| `fora_da_competencia` | data fora de `[inicio, fim]` | `recusado` |
| `duplicata` | repete um item anterior (AMB-007) | `recusado` |
| `categoria_nao_coberta` | categoria não listada na política | `recusado` |
| `valor_invalido` | valor zero ou negativo | `recusado` |

Exemplo, para a entrada reduzida às despesas `d-001` (72,50) e `d-002` (38,00),
ambas alimentação em 2026-07-03:

```json
{
  "politica": "v3",
  "colaborador": {"id": "c-0417", "nome": "Marina Volpi", "centro_custo": "CC-ENG-PLATAFORMA"},
  "periodo": {"competencia": "2026-07", "inicio": "2026-07-01", "fim": "2026-07-31"},
  "itens": [
    {"id": "d-001", "data": "2026-07-03", "categoria": "alimentacao",
     "descricao": "Almoco com cliente", "valor_solicitado": 72.50,
     "valor_reembolsavel": 60.00, "status": "parcial",
     "motivo": "acima_do_limite_diario",
     "detalhe": "limite de alimentacao em 2026-07-03 e R$ 60,00; restavam R$ 60,00"},
    {"id": "d-002", "data": "2026-07-03", "categoria": "alimentacao",
     "descricao": "Jantar apos reuniao", "valor_solicitado": 38.00,
     "valor_reembolsavel": 0.00, "status": "recusado",
     "motivo": "acima_do_limite_diario",
     "detalhe": "limite de alimentacao em 2026-07-03 e R$ 60,00; restavam R$ 0,00"}
  ],
  "resumo": {"total_solicitado": 110.50, "total_reembolsavel": 60.00,
             "aprovados": 0, "parciais": 1, "recusados": 1}
}
```

## 5. Regras de negócio

### RN-001 — Limite diário por categoria

**Regra:** para cada par (data, categoria) existe uma cota: alimentação
R$ 60,00; transporte urbano R$ 80,00; hospedagem R$ 250,00. A soma do
reembolsável dos itens daquele par nunca passa da cota.
**Origem:** política itens 1, 2, 3 · AMB-001, AMB-015
**Aceite:** dois almoços no mesmo dia, 72,50 e 38,00, reembolsam 60,00 no
total; um almoço de 54,90 sozinho reembolsa 54,90.

### RN-002 — Reembolso parcial corta o excedente

**Regra:** item que não cabe inteiro na cota recebe o que resta dela; a cota é
consumida pelos itens elegíveis na ordem em que aparecem na entrada. Reembolso
igual ao valor → `aprovado`; entre zero e o valor → `parcial`; zero → `recusado`.
**Origem:** política item 4 · AMB-002, AMB-003
**Aceite:** alimentação 72,50 → 60,00 `parcial`; o 38,00 seguinte no mesmo
dia → 0,00 `recusado` com motivo `acima_do_limite_diario`.

### RN-003 — Nota fiscal obrigatória acima de R$ 100,00

**Regra:** item com `valor_solicitado` estritamente maior que R$ 100,00 e sem
nota fiscal é recusado inteiro. Exatamente 100,00 não exige nota. O piso é
comparado ao valor solicitado do item, nunca à soma do dia nem ao valor
ampliado por viagem.
**Origem:** política item 5 · AMB-004, AMB-012, AMB-014
**Aceite:** transporte 100,00 sem nota → avaliado normalmente (reembolsa 80,00
pelo limite); transporte 100,01 sem nota → `recusado`, `sem_nota_fiscal`.

### RN-004 — Dia em viagem amplia limites em 50%

**Regra:** num dia em viagem (RN-005) as cotas de RN-001 valem 90,00 /
120,00 / 375,00. A ampliação não altera o piso de nota fiscal.
**Origem:** política item 6 · AMB-014
**Aceite:** café de 33,33 em dia de viagem → `aprovado`; hospedagem de 480,00
→ 375,00 `parcial`.

### RN-005 — Como se reconhece "em viagem"

**Regra:** um dia D está em viagem quando existe na entrada um item de
categoria hospedagem, com valor positivo e data dentro do período, datado de D
ou de D−1 (a diária cobre a noite e o dia seguinte). Vale mesmo que esse item
de hospedagem seja recusado por nota ou duplicata: a estadia é evidência de
viagem independentemente de ser paga.
**Origem:** política item 6 · AMB-005
**Aceite:** hospedagem em 14/07 → 14/07 e 15/07 são dias em viagem; 16/07 não
é. Consequência declarada: todo item de hospedagem é, por definição, avaliado
em dia de viagem (cota 375,00).

### RN-006 — Competência fechada e inclusiva

**Regra:** item com data anterior a `periodo.inicio` ou posterior a
`periodo.fim` é recusado com `fora_da_competencia`. As duas pontas são aceitas.
**Origem:** política item 7 · AMB-006
**Aceite:** data 2026-04-15 num período de julho → `recusado`; 2026-07-31 com
`fim` 2026-07-31 → avaliado normalmente.

### RN-007 — Duplicata: a segunda ocorrência é recusada

**Regra:** dois itens são duplicatas quando têm a mesma data, categoria
normalizada, fornecedor (sem distinção de maiúsculas e espaços nas pontas) e
valor em centavos. O primeiro na ordem da entrada é avaliado; os seguintes são
recusados com `duplicata` e não consomem cota. `id` e `descricao` não entram
na comparação.
**Origem:** política item 8 · AMB-007
**Aceite:** `d-006` e `d-007` (mesma data, Bistro Central, 54,90) → `d-006`
avaliado, `d-007` `recusado` `duplicata`.

### RN-008 — Categoria fora da política não é reembolsável

**Regra:** categorias reconhecidas: `alimentacao`, `transporte_urbano`,
`hospedagem`. Qualquer outra → `recusado`, `categoria_nao_coberta`.
Comparação após normalização (RN-010).
**Origem:** política item 9 · AMB-009, AMB-010
**Aceite:** `coworking` 89,00 → `recusado`.

### RN-009 — Valor zero ou negativo não é despesa

**Regra:** item com valor ≤ 0 após arredondamento → `recusado`,
`valor_invalido`; não abate nem soma a nada.
**Origem:** AMB-008 (lacuna da política)
**Aceite:** "Estorno de corrida" −45,00 → `recusado`, `valor_invalido`;
o total do dia não muda.

### RN-010 — Normalização da entrada

**Regra:** `valor` é arredondado a 2 casas (meio para cima) antes de qualquer
regra; `categoria` e `fornecedor` são comparados em minúsculas e sem espaços
nas pontas. A saída mostra o valor arredondado e a categoria em minúsculas.
**Origem:** AMB-008, AMB-009
**Aceite:** 33,333 → 33,33; "ALIMENTACAO" → tratada como `alimentacao`.

### RN-011 — Um item de hospedagem conta como uma diária

**Regra:** a entrada não informa número de diárias; cada item de hospedagem é
avaliado como uma diária na sua data.
**Origem:** política item 3 · AMB-013
**Aceite:** "Hotel - 2 diárias" 480,00 em dia de viagem → 375,00 `parcial`.

### RN-012 — Resumo

**Regra:** `resumo` soma os valores de todos os itens e conta os status.
**Aceite:** para `exemplos/despesas-exemplo.json`, ver caso E-01 na seção 7.

---

## 6. Ambiguidades identificadas e decisões

### AMB-001 — "Por dia" é por despesa ou por soma do dia? *(unidade de aplicação)*

**Texto original:** "Alimentação tem limite de R$ 60 por dia."
**O que não está claro:** cada almoço tem 60 de teto, ou o dia inteiro tem 60.
`d-001` + `d-002` no mesmo dia somam 110,50.
**Decisão:** a cota é do par (dia, categoria); os itens a consomem em ordem.
**Justificativa:** "por dia" é a unidade que o RH escreveu; por despesa
permitiria dez almoços de 60 num dia, o que esvazia o limite.
**Regra afetada:** RN-001

### AMB-002 — "Parcialmente" corta o excedente ou recusa? *(fronteira)*

**Texto original:** "Despesas acima do limite são reembolsadas parcialmente."
**O que não está claro:** paga até o limite, ou recusa o item inteiro.
**Decisão:** paga o que resta da cota; o excedente é cortado.
**Justificativa:** "parcialmente" significa paga uma parte; recusar inteiro
seria "não são reembolsadas".
**Regra afetada:** RN-002

### AMB-003 — Como dividir a cota entre vários itens do mesmo dia *(unidade de aplicação)*

**Texto original:** (ausente)
**O que não está claro:** com 60 de cota e itens de 72,50 e 38,00, quem leva o
quê: proporcional, o menor primeiro, o primeiro primeiro.
**Decisão:** ordem da entrada, cada item leva o que sobrou.
**Justificativa:** determinístico e explicável item a item; proporcional
produz centavos quebrados e muda quando se adiciona um item.
**Regra afetada:** RN-002

### AMB-004 — "Acima de R$ 100" inclui 100,00? *(fronteira)*

**Texto original:** "Nota fiscal é obrigatória acima de R$ 100."
**O que não está claro:** 100,00 exige nota ou não. `d-003` é 100,00 e
`d-004` é 100,01, ambos sem nota.
**Decisão:** estritamente maior; 100,00 não exige nota.
**Justificativa:** "acima de" em português corrente exclui o próprio valor.
**Regra afetada:** RN-003

### AMB-005 — O que caracteriza "em viagem" *(dado ausente)*

**Texto original:** "Colaborador em viagem tem limites ampliados em 50%."
**O que não está claro:** a entrada não tem campo de viagem.
**Decisão:** dia com hospedagem (ou dia seguinte a uma) é dia em viagem.
**Justificativa:** hospedagem é a única evidência objetiva de viagem presente
nos dados; "Cafe da manha hotel" de `d-011` em 15/07, dia após o hotel de
14/07, é exatamente o caso que a ampliação quer cobrir.
**Regra afetada:** RN-004, RN-005

### AMB-006 — Fronteiras do período de competência *(fronteira)*

**Texto original:** "Despesas devem ser lançadas dentro do período de competência."
**O que não está claro:** se `inicio` e `fim` entram; o que acontece com o
item fora (`d-008`, de abril): recusa, ignora ou avisa.
**Decisão:** intervalo fechado nas duas pontas; item fora é recusado e aparece
na saída com motivo.
**Justificativa:** o financeiro precisa ver o item para relançar na
competência certa; sumir com ele esconde o problema.
**Regra afetada:** RN-006

### AMB-007 — "Duplicatas devem ser tratadas": o que é duplicata e qual é o tratamento *(unidade de aplicação)*

**Texto original:** "Duplicatas devem ser tratadas."
**O que não está claro:** o que torna dois itens iguais (ids diferem sempre),
e se a segunda é recusada, somada ou marcada.
**Decisão:** iguais em data, categoria, fornecedor e valor; a segunda é
recusada e não consome cota.
**Justificativa:** quatro campos iguais no mesmo dia é lançamento repetido,
não duas compras; recusar a segunda (não a primeira) mantém o resultado
estável com a ordem da entrada.
**Regra afetada:** RN-007

### AMB-008 — Valor negativo e valor com mais de duas casas *(fronteira)*

**Texto original:** (ausente; a política só fala em valores positivos)
**O que não está claro:** `d-009` é −45,00 ("estorno"); `d-011` é 33,333.
Negativo abate do dia? Terceira casa arredonda como?
**Decisão:** valor ≤ 0 é recusado como inválido e não abate nada; valores são
arredondados a centavos (meio para cima) na leitura.
**Justificativa:** a política não prevê crédito; compensar estorno contra
outra corrida mascararia dois eventos distintos. Dinheiro só existe em
centavos.
**Regra afetada:** RN-009, RN-010

### AMB-009 — Maiúsculas na categoria *(fronteira)*

**Texto original:** (ausente)
**O que não está claro:** `d-014` vem como `ALIMENTACAO`.
**Decisão:** comparação sem distinção de maiúsculas e espaços nas pontas.
**Justificativa:** é o mesmo conceito digitado diferente; recusar por caixa
alta puniria o colaborador por erro de digitação.
**Regra afetada:** RN-008, RN-010

### AMB-010 — Categoria não listada *(unidade de aplicação)*

**Texto original:** "Categorias fora da política não são reembolsáveis."
**O que não está claro:** `coworking` (`d-005`) com nota e abaixo de 100: é
"fora da política" ou cai em alguma categoria por analogia?
**Decisão:** só as três categorias nomeadas são cobertas; o resto é recusado.
**Justificativa:** analogia é opinião; a lista fechada é verificável.
**Regra afetada:** RN-008

### AMB-011 — Fim de semana e plantão *(dado ausente)*

**Texto original:** (ausente)
**O que não está claro:** `d-012` é um sábado de plantão; limite diferente?
**Decisão:** nenhum tratamento; sábado é um dia como outro.
**Justificativa:** a política não distingue dias; inventar regra de plantão
sem o RH seria legislar.
**Regra afetada:** RN-001

### AMB-012 — Piso da nota fiscal: valor do item ou soma do dia? *(unidade de aplicação)*

**Texto original:** "Nota fiscal é obrigatória acima de R$ 100."
**O que não está claro:** duas corridas de 60 sem nota no mesmo dia somam 120.
**Decisão:** o piso compara o valor do item.
**Justificativa:** nota fiscal é documento de uma compra; não existe nota da
soma do dia.
**Regra afetada:** RN-003

### AMB-013 — Número de diárias da hospedagem *(dado ausente)*

**Texto original:** "Hospedagem tem limite de R$ 250 por diária."
**O que não está claro:** `d-010` descreve "2 diárias" e `d-013` "3 noites",
mas não há campo numérico.
**Decisão:** um item de hospedagem = uma diária; descrição não é interpretada.
**Justificativa:** ler número em texto livre é adivinhação; o custo é
explícito e o financeiro pode lançar uma linha por diária.
**Regra afetada:** RN-011

### AMB-014 — A ampliação de 50% alcança o piso de nota fiscal? *(fronteira)*

**Texto original:** "em viagem tem limites ampliados em 50%" / "obrigatória acima de R$ 100"
**O que não está claro:** se "limites" inclui o piso de 100.
**Decisão:** não; só as cotas diárias (itens 1–3) são ampliadas.
**Justificativa:** o RH chama 100 de obrigação de documento, não de limite.
**Regra afetada:** RN-003, RN-004

### AMB-015 — Hospedagem "por diária" é agregada por dia como as outras? *(unidade de aplicação)*

**Texto original:** "Hospedagem tem limite de R$ 250 por diária."
**O que não está claro:** "diária" é a unidade do hotel, "dia" é a do
calendário; duas hospedagens na mesma data somam ou cada uma tem 250?
**Decisão:** agregada por data como as demais categorias (combinado com RN-011).
**Justificativa:** uma única regra de agregação para todas as categorias;
duas diárias na mesma data é quase sempre lançamento repetido.
**Regra afetada:** RN-001, RN-011

---

## 7. Casos de borda

| Caso | Entrada | Comportamento esperado | Regra |
|---|---|---|---|
| B-01 | alimentação 60,00 em dia comum | 60,00 `aprovado` | RN-001 |
| B-02 | alimentação 60,01 em dia comum | 60,00 `parcial` | RN-002 |
| B-03 | transporte 100,00 sem nota | 80,00 `parcial` (nota não exigida) | RN-003 |
| B-04 | transporte 100,01 sem nota | 0,00 `recusado` `sem_nota_fiscal` | RN-003 |
| B-05 | item sem nota e acima de 100 no mesmo dia de outro item | não consome cota | RN-002, RN-003 |
| B-06 | data = `inicio` ou = `fim` | avaliado normalmente | RN-006 |
| B-07 | data = `inicio` − 1 dia | `fora_da_competencia` | RN-006 |
| B-08 | valor 0,00 | `valor_invalido` | RN-009 |
| B-09 | valor 0,005 | arredonda a 0,01, avaliado | RN-010 |
| B-10 | hospedagem recusada por nota em 22/07 | 22/07 e 23/07 ainda são dias em viagem | RN-005 |
| B-11 | duplicata com `descricao` diferente | ainda é duplicata | RN-007 |
| B-12 | três itens iguais | 1º avaliado, 2º e 3º `duplicata` | RN-007 |
| B-13 | lista `despesas` vazia | saída com `itens: []` e resumo zerado | RN-012 |
| B-14 | `tem_nota_fiscal` ausente | tratado como `false` | 4.1 |
| B-15 | campo obrigatório ausente | erro, sem arquivo de saída | 4.1 |

**E-01 — resultado esperado para `exemplos/despesas-exemplo.json`:**

| id | reembolsável | status | motivo |
|---|---|---|---|
| d-001 | 60,00 | parcial | acima_do_limite_diario |
| d-002 | 0,00 | recusado | acima_do_limite_diario |
| d-003 | 80,00 | parcial | acima_do_limite_diario |
| d-004 | 0,00 | recusado | sem_nota_fiscal |
| d-005 | 0,00 | recusado | categoria_nao_coberta |
| d-006 | 54,90 | aprovado | dentro_do_limite |
| d-007 | 0,00 | recusado | duplicata |
| d-008 | 0,00 | recusado | fora_da_competencia |
| d-009 | 0,00 | recusado | valor_invalido |
| d-010 | 375,00 | parcial | acima_do_limite_diario |
| d-011 | 33,33 | aprovado | dentro_do_limite |
| d-012 | 47,20 | aprovado | dentro_do_limite |
| d-013 | 0,00 | recusado | sem_nota_fiscal |
| d-014 | 60,00 | parcial | acima_do_limite_diario |

Totais: solicitado 1 816,84 (soma aritmética de todos os valores, inclusive o
−45,00 e o 33,33 arredondado); reembolsável 710,43; aprovados 3, parciais 4,
recusados 7.

## 8. Ordem de aplicação das regras

Para cada item, na ordem da entrada, a primeira regra que recusa vence e define
o `motivo`:

1. Normalização (RN-010).
2. Valor inválido (RN-009).
3. Fora da competência (RN-006).
4. Categoria não coberta (RN-008).
5. Duplicata (RN-007) — comparada só contra itens anteriores que chegaram
   até aqui.
6. Nota fiscal (RN-003).
7. Cota diária, com ampliação de viagem (RN-001, RN-002, RN-004, RN-005).

Dias em viagem (RN-005) são calculados antes do passo 7, a partir de todos os
itens de hospedagem que passaram pelos passos 2, 3 e 4.

Itens recusados nos passos 2–6 não consomem cota.

## 9. Critérios de aceite

O sistema está pronto quando:

- [ ] Rodar o comando com `exemplos/despesas-exemplo.json` produz exatamente a
      tabela E-01.
- [ ] Cada RN-001..RN-012 tem ao menos um teste automatizado cujo nome cita a
      regra.
- [ ] Cada caso B-01..B-15 tem teste.
- [ ] Entrada malformada termina com erro e sem arquivo de saída.
- [ ] A saída é a mesma em duas execuções com a mesma entrada.

## 10. O que fica em aberto

- **Diárias de hospedagem:** a decisão "um item = uma diária" (AMB-013) corta
  hospedagens legítimas de várias noites. Resolução correta exige um campo
  `diarias` na entrada; provisório até o RH ou o financeiro definirem.
- **Viagem:** inferir por hospedagem (AMB-005) não cobre viagem de um dia sem
  pernoite. Resolução correta exige um campo `em_viagem` ou um bloco de viagem
  na entrada.
- **Centro de custo:** copiado para a saída e ignorado no cálculo; a política
  v3 não o menciona.
