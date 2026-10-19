# Spec — Motor de Cálculo de Reembolso

**Versão:** 2.0 · **Status:** aprovada para implementação · **Última alteração:** 2026-10-19

> **Versão 2.0** absorve o comunicado "Política de Reembolso v4" do Dia 2 (ver
> `DECISIONS.md` D-003): limites por centro de custo lidos de arquivo, despesas
> em moeda estrangeira e fila de aprovação manual. Tudo que mudou está marcado
> com **[v4]**.

> Este arquivo descreve o QUÊ e o PORQUÊ. Nenhuma linha aqui cita linguagem,
> biblioteca, classe, função ou estrutura de pasta. Solução mora no `plan.md`.
>
> Teste de aceitação da própria spec: uma pessoa que nunca viu o projeto
> consegue, lendo só este arquivo, verificar se o sistema está correto?

---

## 1. Problema

O financeiro confere na mão, item por item, as despesas de cada colaborador
contra a Política de Reembolso do RH (v3; v4 a partir do Dia 2). A política é curta e ambígua, então
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
- Não busca cotação de câmbio em lugar nenhum: usa só a tabela fornecida **[v4]**.
- Não decide a aprovação de itens pendentes; só os marca **[v4]**.
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
| `colaborador.centro_custo` | texto | centro de custo; escolhe a tabela de limites (RN-013) **[v4]** | não (ausente = política padrão) |
| `periodo.competencia` | texto `AAAA-MM` | rótulo do período; copiado para a saída | não |
| `periodo.inicio` | data `AAAA-MM-DD` | primeiro dia aceito (inclusive) | sim |
| `periodo.fim` | data `AAAA-MM-DD` | último dia aceito (inclusive) | sim |
| `despesas[].id` | texto | identificador único do item na saída | sim |
| `despesas[].data` | data `AAAA-MM-DD` | data em que a despesa ocorreu | sim |
| `despesas[].categoria` | texto | categoria; comparação sem distinção de maiúsculas e espaços nas pontas (AMB-009) | sim |
| `despesas[].descricao` | texto | texto livre; copiado para a saída, nunca interpretado | não |
| `despesas[].fornecedor` | texto | quem recebeu; usado na detecção de duplicata | não (ausente = vazio) |
| `despesas[].valor` | número | valor na moeda do item; arredondado a centavos na leitura (AMB-008) | sim |
| `despesas[].moeda` | texto ISO 4217 | moeda do valor; comparação sem distinção de maiúsculas e espaços **[v4]** | não (ausente = `BRL`) |
| `despesas[].tem_nota_fiscal` | booleano | se há nota fiscal | não (ausente = `false`) |

Entrada malformada (JSON inválido, campo obrigatório ausente, data ilegível,
valor não numérico) encerra a execução com erro descritivo e nenhum arquivo de
saída é escrito.

**Arquivo de política [v4]** (opcional): tabela de limites conforme
`exemplos/envelope/politica-v4.json`. Campos usados: `versao`, `padrao`
(categoria → `limite`), `centros_custo` (centro de custo → categoria →
`limite`), `nota_fiscal_obrigatoria_acima_de`, `acrescimo_em_viagem_percentual`.
Os campos `periodicidade`, `observacao`, `vigencia` e `moeda_base` são
ignorados (AMB-024, AMB-028). Quando nenhum arquivo é informado, vale a
política padrão embutida, idêntica à v3 (AMB-027).

**Arquivo de câmbio [v4]** (opcional): conforme `exemplos/envelope/cambio.json`;
`taxas` é data → moeda → quantos reais vale uma unidade da moeda. Quando
nenhum arquivo é informado, só `BRL` é aceito.

### 4.2 Saída

| Campo | Tipo | Significado |
|---|---|---|
| `politica` | texto | versão da política aplicada: `versao` do arquivo, ou `"v3"` para a padrão embutida |
| `colaborador` | objeto | cópia do bloco de entrada |
| `periodo` | objeto | cópia do bloco de entrada |
| `itens[]` | lista | um item por despesa de entrada, na mesma ordem |
| `itens[].id` | texto | id da despesa |
| `itens[].data` | data | data da despesa |
| `itens[].categoria` | texto | categoria normalizada (minúsculas) |
| `itens[].descricao` | texto | cópia |
| `itens[].moeda` | texto | moeda do item, normalizada em maiúsculas **[v4]** |
| `itens[].valor_original` | número (2 casas) | valor na moeda do item, após arredondamento **[v4]** |
| `itens[].taxa_cambio` | número ou nulo | taxa usada; `1` para BRL; nulo quando não houve conversão **[v4]** |
| `itens[].valor_solicitado` | número (2 casas) ou nulo | valor em reais usado nas regras; nulo quando a conversão foi impossível **[v4]** |
| `itens[].valor_reembolsavel` | número (2 casas) | quanto a empresa paga por este item |
| `itens[].status` | texto | `aprovado` (paga tudo), `parcial` (paga parte), `recusado` (paga zero), `pendente` (valor proposto aguarda gestor) **[v4]** |
| `itens[].motivo` | texto | código do motivo (tabela abaixo) |
| `itens[].detalhe` | texto | frase legível explicando o motivo, com os números usados |
| `resumo.total_solicitado` | número | soma de `valor_solicitado` dos itens com valor em reais |
| `resumo.total_reembolsavel` | número | soma de `valor_reembolsavel` dos itens `aprovado` e `parcial` |
| `resumo.total_pendente` | número | soma de `valor_reembolsavel` dos itens `pendente` **[v4]** |
| `resumo.aprovados` / `parciais` / `recusados` / `pendentes` | inteiro | contagem por status |

Códigos de `motivo`:

| Código | Quando | Status resultante |
|---|---|---|
| `dentro_do_limite` | item cabe inteiro na cota do dia | `aprovado` |
| `acima_do_limite_diario` | cota do dia cobre parte ou nada do item | `parcial` ou `recusado` |
| `sem_nota_fiscal` | valor acima do piso de nota e `tem_nota_fiscal` falso | `recusado` |
| `fora_da_competencia` | data fora de `[inicio, fim]` | `recusado` |
| `duplicata` | repete um item anterior (AMB-007) | `recusado` |
| `categoria_nao_coberta` | categoria sem limite na tabela do centro de custo nem na padrão, ou com limite zero (RN-013) | `recusado` |
| `cambio_indisponivel` | moeda sem taxa na data ou antes dela (RN-014) **[v4]** | `recusado` |
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
     "descricao": "Almoco com cliente", "moeda": "BRL", "valor_original": 72.50,
     "taxa_cambio": 1, "valor_solicitado": 72.50,
     "valor_reembolsavel": 60.00, "status": "parcial",
     "motivo": "acima_do_limite_diario",
     "detalhe": "limite de alimentacao em 2026-07-03 e R$ 60,00; restavam R$ 60,00"},
    {"id": "d-002", "data": "2026-07-03", "categoria": "alimentacao",
     "descricao": "Jantar apos reuniao", "moeda": "BRL", "valor_original": 38.00,
     "taxa_cambio": 1, "valor_solicitado": 38.00,
     "valor_reembolsavel": 0.00, "status": "recusado",
     "motivo": "acima_do_limite_diario",
     "detalhe": "limite de alimentacao em 2026-07-03 e R$ 60,00; restavam R$ 0,00"}
  ],
  "resumo": {"total_solicitado": 110.50, "total_reembolsavel": 60.00, "total_pendente": 0.00,
             "aprovados": 0, "parciais": 1, "recusados": 1, "pendentes": 0}
}
```

## 5. Regras de negócio

### RN-001 — Limite diário por categoria

**Regra:** para cada par (data, categoria) existe uma cota, em reais, dada
pela tabela de limites do colaborador (RN-013). Na política padrão: alimentação
R$ 60,00; transporte urbano R$ 80,00; hospedagem R$ 250,00. A soma do
reembolsável dos itens daquele par nunca passa da cota.
**Origem:** política itens 1, 2, 3 · AMB-001, AMB-015 · v4 item A
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

**Regra:** item com `valor_solicitado` (em reais, já convertido) estritamente
maior que o piso e sem nota fiscal é recusado inteiro. Piso padrão R$ 100,00;
exatamente 100,00 não exige nota. O piso é comparado ao valor solicitado do
item, nunca à soma do dia nem ao valor ampliado por viagem.
**Origem:** política item 5 · AMB-004, AMB-012, AMB-014, AMB-022
**Aceite:** transporte 100,00 sem nota → avaliado normalmente (reembolsa 80,00
pelo limite); transporte 100,01 sem nota → `recusado`, `sem_nota_fiscal`.

### RN-004 — Dia em viagem amplia limites em 50%

**Regra:** num dia em viagem (RN-005) as cotas de RN-001 são ampliadas pelo
percentual da política (padrão 50%): 90,00 / 120,00 / 375,00 na padrão. A
ampliação não altera o piso de nota fiscal. Limite zero continua zero.
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

**Regra:** categoria coberta é a que tem limite maior que zero na tabela do
colaborador (RN-013). Na política padrão: `alimentacao`, `transporte_urbano`,
`hospedagem`. Qualquer outra, ou com limite zero → `recusado`,
`categoria_nao_coberta`. Comparação após normalização (RN-010).
**Origem:** política item 9 · AMB-009, AMB-010, AMB-017
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
nas pontas; `moeda` em maiúsculas e sem espaços. A saída mostra o valor
arredondado, a categoria em minúsculas e a moeda em maiúsculas.
**Origem:** AMB-008, AMB-009, AMB-026
**Aceite:** 33,333 → 33,33; "ALIMENTACAO" → tratada como `alimentacao`.

### RN-011 — Um item de hospedagem conta como uma diária

**Regra:** a entrada não informa número de diárias; cada item de hospedagem é
avaliado como uma diária na sua data.
**Origem:** política item 3 · AMB-013
**Aceite:** "Hotel - 2 diárias" 480,00 em dia de viagem → 375,00 `parcial`.

### RN-012 — Resumo

**Regra:** `resumo` soma `valor_solicitado` dos itens com valor em reais,
`valor_reembolsavel` dos aprovados e parciais em `total_reembolsavel`, dos
pendentes em `total_pendente`, e conta cada status.
**Aceite:** para `exemplos/despesas-exemplo.json`, ver caso E-01 na seção 7.

### RN-013 — Limites por centro de custo **[v4]**

**Regra:** a tabela de limites do colaborador é a tabela `padrao` do arquivo
de política sobreposta, categoria a categoria, pela entrada do seu
`centro_custo` em `centros_custo`. Centro de custo ausente na entrada ou sem
entrada no arquivo → só a tabela padrão. Categoria presente só na padrão vale
pela padrão; presente só no centro de custo vale pelo centro de custo; limite
zero significa não reembolsável. Sem arquivo de política, a tabela é a padrão
embutida (igual à v3).
**Origem:** v4 item A · AMB-016, AMB-017, AMB-018, AMB-027
**Aceite:** `CC-ADM` (sem hospedagem na sua entrada) tem hospedagem 250,00;
`CC-ENG-PLATAFORMA` tem hospedagem 0 → item de hospedagem `recusado`
`categoria_nao_coberta`; `CC-SUPORTE-N2` (não listado) tem alimentação 60,00 e
não tem `representacao`.

### RN-014 — Moeda estrangeira e conversão **[v4]**

**Regra:** cada item tem uma moeda (ausente = `BRL`). Item em `BRL` tem taxa
1. Item em outra moeda é convertido para reais multiplicando o valor
arredondado pela taxa da data do item; se não houver taxa publicada naquela
data, usa-se a taxa da data publicada mais recente anterior a ela; se não
houver nenhuma taxa até aquela data, ou a moeda não constar da tabela, o item
é `recusado` com `cambio_indisponivel` e `valor_solicitado` nulo. O resultado
da conversão é arredondado a centavos (meio para cima) uma única vez. Todas as
regras seguintes (nota fiscal, cotas, pendência) usam o valor em reais.
`valor_solicitado` e `taxa_cambio` são preenchidos sempre que a taxa existe,
inclusive em item recusado por valor inválido ou competência; só ficam nulos
quando não há taxa. O
valor inválido (RN-009) e a duplicata (RN-007) olham o valor original e a
moeda.
**Origem:** v4 item B · AMB-019, AMB-020, AMB-021, AMB-022, AMB-023
**Aceite:** 22,00 EUR em 2026-07-14 (taxa 5,93) → 130,46; 30,00 EUR em
2026-07-18 (sábado, sem taxa) → taxa de 2026-07-17 (5,96) → 178,80;
55,00 GBP → `cambio_indisponivel`.

### RN-015 — Pendência de aprovação manual **[v4]**

**Regra:** item cujo reembolsável calculado seja estritamente maior que
R$ 500,00 não é aprovado automaticamente: recebe `status` `pendente`, mantém
`valor_reembolsavel` como valor proposto e o `motivo` que o cálculo deu. Só
`aprovado` e `parcial` entram em `total_reembolsavel`; pendentes entram em
`total_pendente`.
**Origem:** v4 item C · AMB-025
**Aceite:** hospedagem 1 200,00 em `CC-COMERCIAL` em dia de viagem → proposto
600,00, `pendente`, motivo `acima_do_limite_diario`; 500,00 exatos → `aprovado`.

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

### AMB-016 — "Aplica-se a política padrão": por centro de custo ou por categoria? **[v4]** *(unidade de aplicação)*

**Texto original:** "Alguns centros de custo não têm entrada na tabela. Nesse caso, aplica-se a política padrão."
**O que não está claro:** o RH fala do centro de custo sem entrada. E o centro
de custo com entrada mas sem uma categoria (`CC-ADM` não lista hospedagem)?
Hospedagem é 250 (padrão) ou não coberta?
**Decisão:** sobreposição categoria a categoria: o que o centro de custo não
diz, a padrão diz.
**Justificativa:** o financeiro mantém a tabela "sem aviso"; exigir que cada
centro repita a tabela inteira é convite a esquecer uma linha e cortar
reembolso legítimo. Quem quer bloquear uma categoria escreve limite zero,
como `CC-ENG-PLATAFORMA` fez.
**Regra afetada:** RN-013

### AMB-017 — Limite zero é "não reembolsável" ou "parcial de zero"? **[v4]** *(fronteira)*

**Texto original:** `"hospedagem": {"limite": 0.00, "observacao": "nao reembolsavel"}`
**O que não está claro:** pela RN-002, cota zero daria `recusado` com
`acima_do_limite_diario`; a observação diz outra coisa.
**Decisão:** limite zero = categoria não coberta para aquele centro de custo,
motivo `categoria_nao_coberta`.
**Justificativa:** o motivo precisa dizer ao colaborador que não adianta
reduzir o valor; "acima do limite" sugeriria o contrário.
**Regra afetada:** RN-008, RN-013

### AMB-018 — Categoria nova só existe onde a tabela a lista? **[v4]** *(unidade de aplicação)*

**Texto original:** "`CC-COMERCIAL` tem uma categoria nova, `representacao`, que não existia na v3"
**O que não está claro:** `f-003` é `representacao` num centro de custo fora
da tabela. Vale 300 por analogia, ou é fora da política?
**Decisão:** categoria sem limite na tabela do colaborador é não coberta.
**Justificativa:** a mesma regra fechada de AMB-010; a tabela padrão não tem
`representacao`, logo o padrão não a reembolsa.
**Regra afetada:** RN-013

### AMB-019 — "Taxa da data da despesa" quando não há taxa naquela data **[v4]** *(dado ausente)*

**Texto original:** "A conversão usa a taxa da data da despesa, não a taxa de hoje." / "Cotacoes publicadas apenas em dias uteis bancarios."
**O que não está claro:** `e-004` é de sábado 18/07; não há taxa. Recusa,
usa sexta, usa segunda, interpola?
**Decisão:** a última taxa publicada até a data (sexta 17/07).
**Justificativa:** é a convenção de mercado (PTAX vigente no fim de semana é a
da sexta) e é a única das opções que não olha para o futuro.
**Regra afetada:** RN-014

### AMB-020 — Moeda sem taxa na tabela **[v4]** *(dado ausente)*

**Texto original:** (ausente; `e-006` é GBP, a tabela só tem USD e EUR)
**O que não está claro:** recusar, deixar em reais, pedir à mão.
**Decisão:** `recusado`, `cambio_indisponivel`, valor em reais nulo.
**Justificativa:** não existe conversão defensável sem taxa; o item fica
visível para o financeiro completar a tabela e reprocessar.
**Regra afetada:** RN-014

### AMB-021 — Arredondamento da conversão **[v4]** *(fronteira)*

**Texto original:** (ausente)
**O que não está claro:** 14,50 × 5,88 = 85,26 exato, mas 22 × 5,93 em
ponto flutuante não é; onde se arredonda.
**Decisão:** valor original já em centavos × taxa, arredondado a centavos uma
vez, meio para cima.
**Justificativa:** uma única operação de arredondamento, no mesmo critério
de RN-010.
**Regra afetada:** RN-014

### AMB-022 — O piso de nota fiscal compara em qual moeda? **[v4]** *(unidade de aplicação)*

**Texto original:** "Os limites da política são sempre em BRL."
**O que não está claro:** o RH chama de "limites" as cotas; o piso de 100 é
em reais ou na moeda do item? `e-005` é 40 USD (220 em reais) sem nota.
**Decisão:** em reais, após conversão.
**Justificativa:** a política inteira é em reais; 40 USD sem nota é 220 reais
sem nota.
**Regra afetada:** RN-003, RN-014

### AMB-023 — Duplicata entre moedas **[v4]** *(unidade de aplicação)*

**Texto original:** (ausente)
**O que não está claro:** 22 EUR e 130,46 BRL no mesmo dia e fornecedor são
duplicatas?
**Decisão:** não; a chave de duplicata inclui moeda e valor original.
**Justificativa:** lançamento repetido repete o que foi digitado; comparar
valores convertidos cria coincidências falsas.
**Regra afetada:** RN-007, RN-014

### AMB-024 — Vigência "retroativa à competência atual" **[v4]** *(unidade de aplicação)*

**Texto original:** "Vigência imediata, retroativa à competência atual." / `"vigencia": "2026-07-01"`
**O que não está claro:** o arquivo de política vale para datas anteriores à
vigência? Itens de junho num período de julho já caem em RN-006.
**Decisão:** o arquivo informado vale para toda a entrada; `vigencia` é
ignorada.
**Justificativa:** quem roda o cálculo escolhe o arquivo; misturar duas
políticas por data exigiria dois arquivos e uma regra que o RH não escreveu.
**Regra afetada:** RN-013

### AMB-025 — Pendência: estrito, por item, sobre o reembolsável **[v4]** *(fronteira)*

**Texto original:** "Itens cujo valor reembolsável passe de R$ 500 não são mais aprovados automaticamente."
**O que não está claro:** 500,00 exatos; é por item ou por dia; é sobre o
solicitado ou o reembolsável; o item pendente conta no total?
**Decisão:** estritamente maior que 500,00, por item, sobre o reembolsável
calculado; fica fora de `total_reembolsavel` e dentro de `total_pendente`.
**Justificativa:** "passe de" é estrito, "itens" é por item, "valor
reembolsável" é o calculado; somar pendente ao total pagaria antes do gestor.
**Regra afetada:** RN-015

### AMB-026 — Moeda em minúsculas ou com espaços **[v4]** *(fronteira)*

**Texto original:** "campo `moeda` (ISO 4217)"
**Decisão:** normalizar para maiúsculas sem espaços nas pontas; `eur` = `EUR`.
**Justificativa:** mesmo critério de AMB-009.
**Regra afetada:** RN-010, RN-014

### AMB-027 — Sem arquivo de política, o que vale? **[v4]** *(dado ausente)*

**Texto original:** "O motor precisa ler a política de fora, não de dentro do código."
**O que não está claro:** a interface fixa do comando não tem o arquivo; o
que acontece quando ele não é passado.
**Decisão:** o arquivo é opcional; sem ele vale a tabela padrão embutida,
idêntica à v3, e a saída declara `"politica": "v3"`.
**Justificativa:** mantém a interface obrigatória funcionando e deixa
explícito na saída qual política foi usada.
**Regra afetada:** RN-013

### AMB-028 — `periodicidade` "dia" × "diaria" no arquivo **[v4]** *(unidade de aplicação)*

**Texto original:** `"hospedagem": {"limite": 250.00, "periodicidade": "diaria"}`
**Decisão:** ignorada; as duas são agregadas por data (AMB-015, RN-011).
**Justificativa:** mesma decisão já tomada na v3; o arquivo não traz número
de diárias que mudasse isso.
**Regra afetada:** RN-011, RN-013


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
| B-16 **[v4]** | `centro_custo` ausente no colaborador | tabela padrão | RN-013 |
| B-17 **[v4]** | `CC-ADM`, hospedagem 200,00 | 200,00 `aprovado` (padrão supre) | RN-013 |
| B-18 **[v4]** | `CC-ENG-PLATAFORMA`, hospedagem 200,00 | `recusado` `categoria_nao_coberta`; o dia ainda conta como viagem | RN-013, RN-005 |
| B-19 **[v4]** | `moeda: "eur"` | tratado como `EUR` | RN-010 |
| B-20 **[v4]** | EUR em data anterior à primeira taxa | `cambio_indisponivel` | RN-014 |
| B-21 **[v4]** | EUR com taxa só em data anterior | usa a anterior mais recente | RN-014 |
| B-22 **[v4]** | sem arquivo de câmbio, item em USD | `cambio_indisponivel` | RN-014 |
| B-23 **[v4]** | 22 EUR e 130,46 BRL, mesmo dia e fornecedor | não são duplicatas | RN-007 |
| B-24 **[v4]** | reembolsável exatamente 500,00 | `aprovado` | RN-015 |
| B-25 **[v4]** | reembolsável 500,01 | `pendente`, fora de `total_reembolsavel` | RN-015 |

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

**E-02 — `exemplos/envelope/despesas-envelope.json` com `politica-v4.json` e `cambio.json` (CC-COMERCIAL):**

| id | moeda | taxa | solicitado (R$) | reembolsável | status | motivo |
|---|---|---|---|---|---|---|
| e-001 | BRL | 1 | 340,00 | 300,00 | parcial | acima_do_limite_diario |
| e-002 | EUR | 5,93 | 130,46 | 90,00 | parcial | acima_do_limite_diario |
| e-003 | EUR | 5,88 | 85,26 | 85,26 | aprovado | dentro_do_limite |
| e-004 | EUR | 5,96 (de 17/07) | 178,80 | 90,00 | parcial | acima_do_limite_diario |
| e-005 | USD | 5,50 | 220,00 | 0,00 | recusado | sem_nota_fiscal |
| e-006 | GBP | nulo | nulo | 0,00 | recusado | cambio_indisponivel |
| e-007 | BRL | 1 | 1 200,00 | 600,00 | pendente | acima_do_limite_diario |
| e-008 | BRL | 1 | 95,00 | 95,00 | aprovado | dentro_do_limite (dia de viagem, cota 135) |
| e-009 | BRL | 1 | 120,00 | 0,00 | recusado | categoria_nao_coberta |
| e-010 | BRL | 1 | 88,00 | 88,00 | aprovado | dentro_do_limite |

Totais: solicitado 2 457,52; reembolsável 748,26; pendente 600,00;
aprovados 3, parciais 3, recusados 3, pendentes 1. `politica` = `"v4"`.

**E-03 — `exemplos/envelope/despesas-envelope-cc-desconhecido.json` com os mesmos arquivos (CC-SUPORTE-N2, fora da tabela → padrão):**

| id | solicitado (R$) | reembolsável | status | motivo |
|---|---|---|---|---|
| f-001 | 58,00 | 58,00 | aprovado | dentro_do_limite |
| f-002 | 310,00 | 310,00 | aprovado | dentro_do_limite (dia de viagem, cota 375) |
| f-003 | 190,00 | 0,00 | recusado | categoria_nao_coberta |
| f-004 | 65,76 (12 USD × 5,48) | 65,76 | aprovado | dentro_do_limite |

Totais: solicitado 623,76; reembolsável 433,76; pendente 0; aprovados 3,
recusados 1.

## 8. Ordem de aplicação das regras

Para cada item, na ordem da entrada, a primeira regra que recusa vence e define
o `motivo`:

1. Normalização (RN-010).
2. Valor inválido (RN-009), sobre o valor original.
3. Fora da competência (RN-006).
4. Conversão para reais (RN-014) **[v4]**.
5. Categoria não coberta na tabela do colaborador (RN-008, RN-013).
6. Duplicata (RN-007) — comparada só contra itens anteriores que chegaram
   até aqui.
7. Nota fiscal (RN-003), sobre o valor em reais.
8. Cota diária, com ampliação de viagem (RN-001, RN-002, RN-004, RN-005).
9. Pendência (RN-015) **[v4]**, sobre o reembolsável do passo 8.

Dias em viagem (RN-005) são calculados antes do passo 8, a partir de todos os
itens de hospedagem que passaram pelos passos 2 e 3 (o limite da categoria
não importa: a estadia aconteceu).

Itens recusados nos passos 2–7 não consomem cota.

## 9. Critérios de aceite

O sistema está pronto quando:

- [ ] Rodar o comando com `exemplos/despesas-exemplo.json` produz exatamente a
      tabela E-01.
- [ ] Cada RN-001..RN-012 tem ao menos um teste automatizado cujo nome cita a
      regra.
- [ ] Cada caso B-01..B-15 tem teste.
- [ ] Entrada malformada termina com erro e sem arquivo de saída.
- [ ] A saída é a mesma em duas execuções com a mesma entrada.
- [ ] **[v4]** Rodar com os arquivos do envelope produz E-02 e E-03.
- [ ] **[v4]** Rodar `exemplos/despesas-exemplo.json` sem arquivo de política
      continua produzindo E-01.

## 10. O que fica em aberto

- **Diárias de hospedagem:** a decisão "um item = uma diária" (AMB-013) corta
  hospedagens legítimas de várias noites. Resolução correta exige um campo
  `diarias` na entrada; provisório até o RH ou o financeiro definirem.
- **Viagem:** inferir por hospedagem (AMB-005) não cobre viagem de um dia sem
  pernoite. Resolução correta exige um campo `em_viagem` ou um bloco de viagem
  na entrada.
- **Política por data [v4]:** a tabela vale para a entrada inteira (AMB-024).
  Se o financeiro precisar de duas políticas no mesmo período, o motor não
  atende; provisório.
- **Moedas com arredondamento diferente de 2 casas [v4]** (JPY, por exemplo):
  tratadas como tendo centavos; nenhuma aparece nos dados.
