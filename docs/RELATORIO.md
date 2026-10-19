# Relatório — Desafio SDD

**Aluno:** Peres Juliao · **Repositório:** https://github.com/peresjuliao/sdd-desafio · **Data:** 2026-10-19

> Evidências, não redação. Hashes citados são do `git log` deste repositório.
> Trechos de sessão apontam para `docs/sessions/`.
>
> **Nota de honestidade sobre como este projeto foi feito.** Todo o trabalho
> técnico (spec, plano, tasks, código, testes, absorção do envelope e o
> rascunho deste relatório) foi feito pelo Claude Code numa única sessão
> autônoma de cerca de 25 minutos (commits `03d7b37` 17:03 → `dee0090`
> 17:17, mais o commit do template às 16:57), a partir de um briefing que eu
> escrevi em outra sessão. Eu não revisei o diff em tempo real. Os erros
> registrados na seção Discernimento foram cometidos pelo agente e pegos
> **por verificação automatizada que o próprio agente rodou** (teste, execução
> da CLI), não por mim lendo o código. Onde o template pergunta algo que só eu
> posso responder, o campo está marcado `<<PREENCHER>>` e eu respondo antes de
> entregar; onde está respondido, a resposta vem do registro do repositório.

---

## Delegação

**A divisão:**

| Atividade | Quem | Por quê |
|---|---|---|
| Identificar ambiguidades | Claude, a partir da política × `despesas-exemplo.json` item a item | é leitura sistemática; o agente faz sem pular linha |
| Decidir as ambiguidades | Claude propôs e decidiu; eu aceito ou troco antes da entrega (`<<PREENCHER>>`: quais troquei) | as 28 decisões estão escritas e justificadas em `spec.md` seção 6; cada uma é revisável sem reler código |
| Escrever a spec | Claude | o conteúdo é a tabela de decisões; o texto é consequência |
| Desenhar a arquitetura | Claude, com restrição minha de "stdlib, sem dependência, sem over-engineering" | `plan.md` DT-001..DT-005 |
| Implementar | Claude | 10 pontos em 100; não vale minha atenção além de ler |
| Escrever testes | Claude, com nomes amarrados aos IDs da spec | a rastreabilidade exige esse acoplamento; feito à mão eu esqueceria casos |
| Absorver o envelope | Claude, na ordem spec → DECISIONS → tasks → código | ver seção "O envelope" |

**Onde deleguei e me arrependi:** o relatório. Um relatório escrito pelo mesmo
agente que escreveu o código tem a tendência de contar uma história limpa.
Por isso esta versão tem a nota de honestidade no topo e campos
`<<PREENCHER>>` em vez de prosa inventada sobre a minha experiência.

**Onde não deleguei e deveria ter delegado:** a tentativa de criar o fork pelo
`gh` falhou (máquina sem login) e consumiu tempo da sessão; deveria ter feito
o fork à mão antes de iniciar o agente.

**Usei subagentes / skills / MCP / hooks?** Sim: a sessão rodou com o plugin
`ponytail` (modo "lazy senior dev": stdlib primeiro, sem abstração especulativa).
Valeu: o motor inteiro é uma função de ~40 linhas e o projeto tem zero
dependências. Não usei subagentes: o problema cabe numa conversa só.

---

## Descrição

Requisito escolhido: **"Colaborador em viagem tem limites ampliados em 50%"**
(política item 6), o único que depende de um dado que a entrada não traz.

**Versão 1 (primeira escrita, sessão `docs/sessions/01-*.md`, antes da spec):**
> ```
> "Em viagem": a entrada não tem campo de viagem. Decisão: inferir por hospedagem.
> Um dia D está em viagem se existe hospedagem datada de D ou D-1.
> ```

**Versão final (`spec.md` RN-005, commit `03d7b37`, inalterada até `dee0090`):**
> ```
> um dia D está em viagem quando existe na entrada um item de categoria
> hospedagem, com valor positivo e data dentro do período, datado de D ou de
> D−1 (a diária cobre a noite e o dia seguinte). Vale mesmo que esse item de
> hospedagem seja recusado por nota ou duplicata: a estadia é evidência de
> viagem independentemente de ser paga.
> Consequência declarada: todo item de hospedagem é, por definição, avaliado
> em dia de viagem (cota 375,00).
> ```

**O que estava ambíguo:** (1) o que é "em viagem" sem campo; (2) se uma
hospedagem recusada (sem nota, `d-013`) ainda prova viagem; (3) se hospedagem
fora da competência marca viagem; (4) a consequência de que hospedagem nunca
é avaliada com 250, sempre com 375.

**Como percebi:** olhando `d-011` ("Cafe da manha hotel", 15/07) logo depois
de `d-010` (hotel, 14/07) no JSON de exemplo: a ampliação só faz sentido se o
dia seguinte ao hotel contar. Os pontos (2) e (3) apareceram ao escrever os
testes `test_b_10_hospedagem_recusada_ainda_marca_viagem` e
`test_rn_005_hospedagem_fora_da_competencia_nao_marca_viagem` (commit
`76e2de2`); o ponto (4) ao calcular o E-01 e ver `d-010` → 375.

**Commit da mudança:** `03d7b37` (spec 1.0). A frase sobre limite zero e
viagem foi reafirmada na 2.0 em B-18 (`1889e9f`), quando a política v4 trouxe
`CC-ENG-PLATAFORMA` com hospedagem 0: a estadia continua marcando viagem.

**Prova pelo histórico:** `git log -p --follow specs/001-motor-reembolso/spec.md | grep -n "RN-005"`.

---

## Discernimento

> Os três casos abaixo são erros do agente detectados por verificação que o
> próprio agente executou (rodar a CLI, rodar a suíte). Eu não os detectei
> lendo; a correção pode pesar isso como quiser. São verificáveis no `git log`
> e em `docs/sessions/01-*.md`.

### Caso 1 — A spec dizia uma contagem; a tabela da própria spec dizia outra

**O que ele propôs:** na spec 1.0 (`03d7b37`), a linha de totais do caso E-01
dizia "aprovados 3, parciais 5, recusados 6".

**Por que estava errado:** a tabela item a item logo acima dá 4 parciais
(d-001, d-003, d-010, d-014) e 7 recusados. A linha de totais foi escrita "de
cabeça" e não derivada da tabela.

**Como foi detectado:** ao rodar a CLI recém-pronta (T-010) sobre o exemplo
oficial, o resumo imprimiu `4 parciais, 7 recusados`. O agente conferiu a
tabela antes de "corrigir" o código, viu que a tabela estava certa e que a
linha de totais estava errada.

**O que foi feito:** spec corrigida com entrada `D-002` em `DECISIONS.md`
(commit `92da7a5`) **antes** de escrever o teste ponta a ponta (`fed47e3`),
que compara a tabela e o resumo corrigido.

**Onde está a evidência:** `docs/sessions/01-*.md`, trecho "Achei um erro meu
na spec: a linha de totais do E-01"; `git show 92da7a5`.

### Caso 2 — Teste que testava a coisa errada, e um commit que entrou quebrado

**O que ele propôs:** no teste `test_b_18_hospedagem_limite_zero_ainda_marca_viagem`
(commit `f24a4ae`), a asserção comparava o reembolsável com a **cota
ampliada** (`7500 * 150 // 100` = 112,50) em vez do **valor pago** (100,00).
O comentário na mesma linha dizia "paga 100"; o código do teste dizia 112,50.

**Por que estava errado:** o motor estava certo (paga 100, o item é de 100);
o teste é que afirmava o número errado. Pior: o commit entrou com o teste
falhando, porque o comando de verificação era
`python3 -m unittest ... | tail -1 && git commit`, e o exit code de um pipe é
o do `tail`.

**Como foi detectado:** na rodada seguinte o agente rodou a suíte sem o pipe e
viu `FAILED (failures=1)`.

**O que foi feito:** teste corrigido num commit próprio com a mensagem dizendo
o que aconteceu (`532617b`: "o commit anterior entrou com o teste quebrado
porque o exit code ficou escondido atrás de um pipe"). O histórico não foi
reescrito. Dali em diante toda verificação checou `$?` explicitamente.

**Onde está a evidência:** `docs/sessions/01-*.md`, trecho "A failure got
committed because my pipe masked the exit code"; `git show 532617b`.

### Caso 3 — Ordem de regras lida como ordem de cálculo

**O que ele propôs:** ao implementar a conversão de moeda (T-013) como
"passo 4" da ordem da spec, itens recusados nos passos 2 e 3 (valor negativo,
fora da competência) ficaram sem valor em reais, e o `total_solicitado` do
E-01 mudou de 1 816,84 para 1 820,84.

**Por que estava errado:** a seção 8 da spec é ordem de **precedência dos
motivos**, não ordem em que os números são calculados. Um item recusado
continua tendo sido pedido e precisa aparecer no total solicitado.

**Como foi detectado:** o teste ponta a ponta do E-01 quebrou.

**O que foi feito:** spec esclarecida (RN-014 ganhou uma frase) com `D-004`
(`d06b425`), e só então o motor passou a converter antes das regras
(`f691717`).

**Padrão que eu notei:** os três erros são do mesmo tipo: o agente escreve um
número ou uma asserção "de cabeça" e ela parece certa. O que pega é sempre
uma execução contra um resultado esperado escrito **antes** (a tabela E-01).
Sinal de alerta: qualquer número na spec ou no teste que não foi derivado
de uma conta mostrada.

---

## Diligência

**Meu procedimento de verificação:** `<<PREENCHER>>` — o que eu de fato fiz
antes de entregar: rodei `python3 -m unittest discover -s tests -v`? Li a
seção 6 da spec inteira? Li `motor.py`?

**Li o diff inteiro em que porcentagem das entregas?** `<<PREENCHER>>` (a
resposta honesta para a sessão 01, enquanto ela rodava, é 0%: o agente
trabalhou sozinho).

**O que aceitei sem verificar direito, e o que me custou:** `<<PREENCHER>>`.

**Testes: quem escreveu, e como você sabe que eles testam a coisa certa?** O
agente escreveu código e testes. Duas defesas contra "teste que passa com
facilidade": (1) os resultados esperados E-01, E-02 e E-03 foram escritos na
spec **antes** do código correspondente (commits `03d7b37` e `1889e9f`
precedem `abaa8f4`/`fed47e3` e `f24a4ae`..`6b2b97a`), e os testes ponta a
ponta comparam com essas tabelas copiadas, não com a saída do programa;
(2) o Caso 2 acima mostra que um teste errado foi pego porque falhou, não
porque alguém leu. O que isso **não** cobre: um erro simétrico (spec errada e
código igualmente errado) passaria. O Caso 1 foi exatamente isso quase
acontecendo.

---

## O envelope

**Quantos arquivos toquei na mão:** zero na mão; 18 arquivos pelo agente
(`git diff 8eaea62 dee0090 --stat`), sendo 6 de documentação, 6 de código e
6 de teste.

**Quanto tempo levou:** 7 minutos de relógio entre o commit da spec 2.0
(`1889e9f`, 17:12) e o fechamento de T-015 (`08a41b9`, 17:17), mais ~2
minutos antes disso para ler o envelope e escrever a spec.

**Diff de absorção:** 18 arquivos, +825/−90 linhas no total
(`git diff 8eaea62 dee0090 --stat`). Código de produção (`src/`): 6 arquivos,
+137/−28, um módulo novo (`cambio.py`, 37 linhas). Testes: 6 arquivos,
+238/−4.

**Absorveu de graça:**
- A política já era um dicionário injetado no motor (plan 1.0, seção 4).
  Ler o JSON do financeiro virou uma função que produz o mesmo dicionário;
  o motor não soube que a origem mudou.
- Os valores já eram inteiros em centavos com conversão só nas bordas
  (DT-001); a conversão de moeda entrou como mais uma conversão na borda.
- A ordem de regras estava numa única função (DT-002); inserir "conversão"
  como passo 4 e "pendência" como passo 9 foi editar essa função e a seção 8.
- Os testes da 1.0 continuaram passando com o mesmo resultado; dois mudaram
  de forma (campos novos no resumo) e nenhum de valor. O E-01 é idêntico com
  ou sem `--politica`.

**Resistiu:**
- "Categoria coberta" era "a chave existe na tabela"; com limite zero na v4
  virou "limite > 0". Uma linha, mas é regra de negócio que a 1.0 não previu
  (AMB-017).
- A chave de duplicata precisou da moeda (AMB-023); a 1.0 tinha "valor"
  como se fosse sempre reais.
- O Caso 3 do Discernimento: a ordem de precedência não dizia onde calcular
  a conversão; precisou de D-004.

**Ordem em que fiz:** spec (`1889e9f`) → DECISIONS (`3c47d22`) → tasks
(`88a6132`) → código (`f24a4ae` em diante). Os timestamps confirmam.

**Se eu tivesse escrito a spec original sabendo desta mudança:** teria
escrito RN-008 como "limite maior que zero" desde o início e a chave de
duplicata com moeda. Não teria lido política de arquivo na 1.0: o FAQ avisa
contra arquitetura genérica no lugar errado, e o custo de fazer depois foi
uma função.

**O que a spec me poupou, em concreto:** os resultados esperados E-02 e E-03
foram escritos à mão na spec antes do código, e o código bateu com eles na
primeira execução. Sem isso, "funciona" seria "não deu erro".

**Bônus (números):** das 4 tasks do envelope, 3 (T-012, T-013, T-014) foram
"reexecutar a task a partir da spec": o agente leu a RN nova e escreveu
código + teste; 1 (T-015) foi edição de documentação e CLI. Nenhum arquivo
foi editado à mão por mim.

---

## Fechamento

**Para qual tamanho de projeto isto valeu a pena?** Para este: um motor de
regras com 28 decisões de interpretação. Sem a seção 6 da spec, cada decisão
estaria num `if` e ninguém saberia que era uma decisão.

**Para qual não valeria?** Para um script de uma tarde sem regra de negócio;
a cerimônia (tasks, DECISIONS, commits por task) custaria mais que o código.

**O que eu faria diferente:** `<<PREENCHER>>`.

**A coisa mais desconfortável que aprendi sobre como eu trabalho com IA:**
`<<PREENCHER>>` (sugestão honesta: que o agente fez o trabalho inteiro
sozinho e que a minha contribuição real foi o briefing e esta revisão).

---

## Sessões exportadas

| Arquivo | Conteúdo |
|---|---|
| `docs/sessions/01-spec-codigo-envelope.md` | sessão autônoma: leitura do enunciado, spec 1.0, plano, tasks, T-001..T-011, envelope (spec 2.0, T-012..T-015), rascunho deste relatório |
| `docs/sessions/02-revisao-e-entrega.md` | `<<PREENCHER>>`: minha revisão, ajustes, push |

**Lacuna declarada:** não houve sessão de "Dia 1" separada; tudo foi feito
em 2026-10-19 porque comecei no último dia.
