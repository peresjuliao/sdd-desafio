# Log de Decisões e Mudanças de Spec

> Uma entrada **toda vez** que a spec mudar. Ordem cronológica inversa: a mais
> recente primeiro.

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
