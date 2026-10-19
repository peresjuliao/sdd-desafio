# Tasks — Motor de Cálculo de Reembolso

> Cada task é pequena o bastante para virar **um commit**. Critério de aceite
> é sempre "o teste X passa". Marcar `[x]` ao concluir, junto com o commit.

**Formato do commit:** `feat(T-003): <descrição>` · `test(T-003): <descrição>`

---

## Fase 1 — Fundação

- [x] **T-001** — Leitura e validação da entrada: JSON → `Pedido` com datas e
  centavos; campos obrigatórios; defaults de `tem_nota_fiscal` e `fornecedor`.
  - **Atende:** spec 4.1, RN-010 (arredondamento), B-09, B-14, B-15
  - **Aceite:** `test_rn_010_valor_arredonda_meio_para_cima`,
    `test_b_09_meio_centavo_arredonda_para_cima`, `test_b_14_nota_ausente_e_false`,
    `test_b_15_campo_obrigatorio_ausente_levanta_erro`
  - **Commit:** `cc9d421`

- [x] **T-002** — Política v3 como dados e esqueleto do motor: `calcular`
  devolve um item por despesa, na mesma ordem, com `aprovado`/`dentro_do_limite`
  quando nada recusa; resumo.
  - **Atende:** RN-012, B-13, spec 4.2 (estrutura)
  - **Aceite:** `test_rn_012_resumo_soma_e_conta`, `test_b_13_sem_despesas`
  - **Commit:** `79a4eaf`

## Fase 2 — Regras de negócio

- [ ] **T-003** — Normalização de categoria/fornecedor e categoria não coberta.
  - **Atende:** RN-008, RN-010, AMB-009, AMB-010
  - **Aceite:** `test_rn_008_categoria_fora_da_politica_recusada`,
    `test_rn_010_categoria_maiuscula_e_normalizada`
  - **Commit:**

- [ ] **T-004** — Valor zero ou negativo recusado como inválido.
  - **Atende:** RN-009, AMB-008, B-08
  - **Aceite:** `test_rn_009_estorno_negativo_recusado_e_nao_abate`,
    `test_b_08_valor_zero_invalido`
  - **Commit:**

- [ ] **T-005** — Competência fechada e inclusiva.
  - **Atende:** RN-006, AMB-006, B-06, B-07
  - **Aceite:** `test_rn_006_fora_da_competencia_recusado`,
    `test_b_06_pontas_do_periodo_aceitas`, `test_b_07_dia_antes_do_inicio_recusado`
  - **Commit:**

- [ ] **T-006** — Duplicata: segunda ocorrência recusada, não consome cota.
  - **Atende:** RN-007, AMB-007, B-11, B-12
  - **Aceite:** `test_rn_007_segunda_ocorrencia_e_duplicata`,
    `test_b_11_descricao_diferente_ainda_e_duplicata`,
    `test_b_12_tres_iguais_recusa_duas`
  - **Commit:**

- [ ] **T-007** — Nota fiscal obrigatória acima de 100,00 (estrito, sobre o
  valor do item).
  - **Atende:** RN-003, AMB-004, AMB-012, B-03, B-04
  - **Aceite:** `test_rn_003_cem_reais_exatos_nao_exige_nota`,
    `test_rn_003_cem_e_um_centavo_sem_nota_recusado`
  - **Commit:**

- [ ] **T-008** — Cota diária por (data, categoria) consumida em ordem; corte
  do excedente; status aprovado/parcial/recusado.
  - **Atende:** RN-001, RN-002, AMB-001, AMB-002, AMB-003, AMB-015, B-01, B-02, B-05
  - **Aceite:** `test_rn_001_dois_almocos_somam_na_cota_do_dia`,
    `test_rn_002_excedente_e_cortado_e_segundo_item_zera`,
    `test_b_05_item_sem_nota_nao_consome_cota`, `test_rn_011_hospedagem_e_uma_diaria`
  - **Commit:**

- [ ] **T-009** — Dias em viagem por hospedagem (D e D+1) e ampliação de 50%
  das cotas; piso de nota inalterado.
  - **Atende:** RN-004, RN-005, RN-011, AMB-005, AMB-013, AMB-014, B-10
  - **Aceite:** `test_rn_005_dia_seguinte_a_hospedagem_e_viagem`,
    `test_rn_004_viagem_amplia_cota_em_50`,
    `test_rn_004_viagem_nao_amplia_piso_de_nota`,
    `test_b_10_hospedagem_recusada_ainda_marca_viagem`
  - **Commit:**

## Fase 3 — Saída e CLI

- [ ] **T-010** — Serialização da saída (reais com 2 casas, `detalhe`
  legível) e CLI `calcular --input --output`; erro de entrada sai com código 2
  e sem arquivo.
  - **Atende:** spec 4.2, 4.1 (erro), DT-004
  - **Aceite:** `test_cli_escreve_saida_no_schema`,
    `test_cli_entrada_invalida_nao_escreve_saida`
  - **Commit:**

- [ ] **T-011** — Ponta a ponta com `exemplos/despesas-exemplo.json` igual à
  tabela E-01; README do projeto; CLAUDE.md com comandos reais.
  - **Atende:** spec 9 (critérios de aceite), E-01
  - **Aceite:** `test_e_01_exemplo_oficial_bate_com_a_spec`
  - **Commit:**

---

## Fase 4 — Envelope (criar no Dia 2)

<Numeração continua de T-012.>

---

## Cobertura

| Regra da spec | Task | Teste |
|---|---|---|
| RN-001 | T-008 | `test_rn_001_dois_almocos_somam_na_cota_do_dia` |
| RN-002 | T-008 | `test_rn_002_excedente_e_cortado_e_segundo_item_zera` |
| RN-003 | T-007 | `test_rn_003_cem_reais_exatos_nao_exige_nota`, `test_rn_003_cem_e_um_centavo_sem_nota_recusado` |
| RN-004 | T-009 | `test_rn_004_viagem_amplia_cota_em_50`, `test_rn_004_viagem_nao_amplia_piso_de_nota` |
| RN-005 | T-009 | `test_rn_005_dia_seguinte_a_hospedagem_e_viagem` |
| RN-006 | T-005 | `test_rn_006_fora_da_competencia_recusado` |
| RN-007 | T-006 | `test_rn_007_segunda_ocorrencia_e_duplicata` |
| RN-008 | T-003 | `test_rn_008_categoria_fora_da_politica_recusada` |
| RN-009 | T-004 | `test_rn_009_estorno_negativo_recusado_e_nao_abate` |
| RN-010 | T-001, T-003 | `test_rn_010_valor_arredonda_meio_para_cima`, `test_rn_010_categoria_maiuscula_e_normalizada` |
| RN-011 | T-008 | `test_rn_011_hospedagem_e_uma_diaria` |
| RN-012 | T-002 | `test_rn_012_resumo_soma_e_conta` |
| AMB-001..003, 015 | T-008 | (via RN-001/002/011) |
| AMB-004, 012 | T-007 | (via RN-003) |
| AMB-005, 013, 014 | T-009 | (via RN-004/005) |
| AMB-006 | T-005 | (via RN-006) |
| AMB-007 | T-006 | (via RN-007) |
| AMB-008 | T-001, T-004 | (via RN-009/010) |
| AMB-009, 010 | T-003 | (via RN-008/010) |
| AMB-011 | — | sem comportamento próprio; coberto por E-01 (`d-012` é sábado) |
| B-01..B-15 | T-001..T-009 | `test_b_NN_*` |
| E-01 | T-011 | `test_e_01_exemplo_oficial_bate_com_a_spec` |
