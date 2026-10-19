# Log de Decisões e Mudanças de Spec

> Uma entrada **toda vez** que a spec mudar. Ordem cronológica inversa: a mais
> recente primeiro.

---

## D-003 — Política v4: limites por centro de custo, moeda estrangeira, pendência · 2026-10-19

**Gatilho:** envelope lacrado do Dia 2 (`exemplos/envelope/00-ENVELOPE-LACRADO.md`).

**O que mudou na spec (1.1 → 2.0):**
- Fora de escopo: sai "não trata moeda estrangeira"; entram "não busca cotação" e "não decide pendências".
- Entrada: `centro_custo` passa a escolher a tabela de limites; novo campo opcional `moeda` (ausente = BRL); dois arquivos opcionais, política e câmbio.
- Saída: `politica` vem do arquivo; itens ganham `moeda`, `valor_original`, `taxa_cambio`; `valor_solicitado` pode ser nulo; novo status `pendente`; novo motivo `cambio_indisponivel`; resumo ganha `total_pendente` e `pendentes`.
- RN-001, RN-003, RN-004, RN-008, RN-010, RN-012 reescritas para "a tabela do colaborador" em vez de valores fixos e para o valor em reais.
- Novas RN-013 (centro de custo), RN-014 (conversão), RN-015 (pendência).
- Novas AMB-016..AMB-028 (13 ambiguidades da v4).
- Casos B-16..B-25; resultados esperados E-02 e E-03.
- Ordem de aplicação: conversão entra como passo 4, pendência como passo 9.

**Por quê:** comunicado do RH com vigência imediata. Os três itens (A, B, C)
foram absorvidos; C era opcional e coube porque é uma regra de uma linha sobre
o resultado já calculado.

**O que isso invalidou:**
- A decisão do `plan.md` seção 4 ("uma só política, constante no código").
  Mantida como padrão embutido; o arquivo passa a ser opcional.
- O escopo negativo "não trata moeda estrangeira".
- O exemplo de saída da seção 4.2 e o teste de schema da CLI (ganham campos novos).
- Nenhum resultado do E-01 muda: a política padrão embutida é idêntica à v3.
  `categoria_nao_coberta` passou a cobrir também limite zero, sem efeito no E-01.

**Tasks afetadas:** nenhuma refeita; T-010 e T-011 recebem campos novos na
saída via T-012..T-015. Novas: T-012 (política de arquivo e centro de custo),
T-013 (moeda e câmbio), T-014 (pendência), T-015 (CLI, E-02/E-03, README).

**Custo:** registrado no relatório (`docs/RELATORIO.md`, seção "O envelope"),
com `git diff 8eaea62 HEAD --stat`.

---

## D-002 — Contagem de status do caso E-01 estava errada · 2026-10-19

**Gatilho:** erro descoberto na implementação. Ao rodar a CLI (T-010) sobre
`exemplos/despesas-exemplo.json`, o resumo deu 4 parciais e 7 recusados; a
linha de totais do E-01 dizia 5 e 6. Conferindo a própria tabela item a item
do E-01: parciais são d-001, d-003, d-010, d-014 (4); recusados são d-002,
d-004, d-005, d-007, d-008, d-009, d-013 (7). A tabela estava certa; a linha de
totais, escrita de cabeça, estava errada.

**O que mudou na spec:** seção 7, totais do E-01: "parciais 5, recusados 6" →
"parciais 4, recusados 7". Versão 1.0 → 1.1.

**Por quê:** a tabela é a fonte; a linha de totais é derivada dela e tinha
erro aritmético.

**O que isso invalidou:** nada no código. Se o teste ponta a ponta (T-011)
tivesse sido escrito contra a linha de totais em vez da tabela, teria
"provado" um bug que não existia.

**Tasks afetadas:** T-011 (o teste compara a tabela e o resumo corrigido).

**Custo:** 1 arquivo, minutos.

---

## D-001 — Spec 1.0 fechada · 2026-10-19

**Gatilho:** início do desafio. Leitura da política v3 cruzada com
`exemplos/despesas-exemplo.json`, item por item.

**O que mudou na spec:** criação. 12 regras (RN-001..RN-012), 15 ambiguidades
(AMB-001..AMB-015), 15 casos de borda, resultado esperado E-01.

**Por quê:** não existe spec anterior.

**O que isso invalidou:** nada.

**Tasks afetadas:** T-001..T-011 criadas a partir dela.

**Custo:** uma sessão de leitura e escrita; nenhum código existia.
