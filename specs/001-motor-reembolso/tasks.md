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

- [x] **T-003** — Normalização de categoria/fornecedor e categoria não coberta.
  - **Atende:** RN-008, RN-010, AMB-009, AMB-010
  - **Aceite:** `test_rn_008_categoria_fora_da_politica_recusada`,
    `test_rn_010_categoria_maiuscula_e_normalizada`
  - **Commit:** `5a7a27e`

- [x] **T-004** — Valor zero ou negativo recusado como inválido.
  - **Atende:** RN-009, AMB-008, B-08
  - **Aceite:** `test_rn_009_estorno_negativo_recusado_e_nao_abate`,
    `test_b_08_valor_zero_invalido`
  - **Commit:** `27d6315`

- [x] **T-005** — Competência fechada e inclusiva.
  - **Atende:** RN-006, AMB-006, B-06, B-07
  - **Aceite:** `test_rn_006_fora_da_competencia_recusado`,
    `test_b_06_pontas_do_periodo_aceitas`, `test_b_07_dia_antes_do_inicio_recusado`
  - **Commit:** `fcaa957`

- [x] **T-006** — Duplicata: segunda ocorrência recusada, não consome cota.
  - **Atende:** RN-007, AMB-007, B-11, B-12
  - **Aceite:** `test_rn_007_segunda_ocorrencia_e_duplicata`,
    `test_b_11_descricao_diferente_ainda_e_duplicata`,
    `test_b_12_tres_iguais_recusa_duas`
  - **Commit:** `7fb28ee`

- [x] **T-007** — Nota fiscal obrigatória acima de 100,00 (estrito, sobre o
  valor do item).
  - **Atende:** RN-003, AMB-004, AMB-012, B-03, B-04
  - **Aceite:** `test_rn_003_cem_reais_exatos_nao_exige_nota`,
    `test_rn_003_cem_e_um_centavo_sem_nota_recusado`
  - **Commit:** `8d34d60`

- [x] **T-008** — Cota diária por (data, categoria) consumida em ordem; corte
  do excedente; status aprovado/parcial/recusado.
  - **Atende:** RN-001, RN-002, AMB-001, AMB-002, AMB-003, AMB-015, B-01, B-02, B-05
  - **Aceite:** `test_rn_001_dois_almocos_somam_na_cota_do_dia`,
    `test_rn_002_excedente_e_cortado_e_segundo_item_zera`,
    `test_b_05_item_sem_nota_nao_consome_cota`
  - **Commit:** `9be2dc2`

- [x] **T-009** — Dias em viagem por hospedagem (D e D+1) e ampliação de 50%
  das cotas; piso de nota inalterado.
  - **Atende:** RN-004, RN-005, RN-011, AMB-005, AMB-013, AMB-014, B-10
  - **Aceite:** `test_rn_005_dia_seguinte_a_hospedagem_e_viagem`,
    `test_rn_004_viagem_amplia_cota_em_50`,
    `test_rn_004_viagem_nao_amplia_piso_de_nota`,
    `test_b_10_hospedagem_recusada_ainda_marca_viagem`
  - **Commit:** `76e2de2`

## Fase 3 — Saída e CLI

- [x] **T-010** — Serialização da saída (reais com 2 casas, `detalhe`
  legível) e CLI `calcular --input --output`; erro de entrada sai com código 2
  e sem arquivo.
  - **Atende:** spec 4.2, 4.1 (erro), DT-004
  - **Aceite:** `test_cli_escreve_saida_no_schema`,
    `test_cli_entrada_invalida_nao_escreve_saida`
  - **Commit:** `abaa8f4`

- [x] **T-011** — Ponta a ponta com `exemplos/despesas-exemplo.json` igual à
  tabela E-01; README do projeto; CLAUDE.md com comandos reais.
  - **Atende:** spec 9 (critérios de aceite), E-01
  - **Aceite:** `test_e_01_exemplo_oficial_bate_com_a_spec`
  - **Commit:** `fed47e3`

---

## Fase 4 — Envelope (Dia 2, spec 2.0, D-003)

- [x] **T-012** — Política lida de arquivo e tabela de limites por centro de
  custo (sobreposição categoria a categoria; limite zero = não coberta);
  política padrão embutida quando não há arquivo.
  - **Atende:** RN-013, RN-008 (limite zero), AMB-016, AMB-017, AMB-018, AMB-024, AMB-027, AMB-028, B-16, B-17, B-18
  - **Aceite:** `test_rn_013_cc_sem_entrada_usa_padrao`, `test_rn_013_cc_sobrepoe_categoria_a_categoria`,
    `test_rn_013_limite_zero_e_categoria_nao_coberta`, `test_b_18_hospedagem_limite_zero_ainda_marca_viagem`,
    `test_rn_013_representacao_so_onde_listada`
  - **Commit:** `f24a4ae`

- [ ] **T-013** — Campo `moeda` e conversão pela taxa da data (ou a anterior
  mais recente); `cambio_indisponivel`; piso de nota e cotas sobre o valor em
  reais; duplicata sobre moeda e valor original.
  - **Atende:** RN-014, RN-010 (moeda), RN-003/RN-007 (ajustes), AMB-019..AMB-023, AMB-026, B-19..B-23
  - **Aceite:** `test_rn_014_converte_pela_taxa_da_data`, `test_rn_014_sem_taxa_na_data_usa_anterior_mais_recente`,
    `test_rn_014_moeda_sem_taxa_e_cambio_indisponivel`, `test_b_20_data_anterior_a_primeira_taxa`,
    `test_amb_022_piso_de_nota_sobre_valor_em_reais`, `test_b_23_moedas_diferentes_nao_sao_duplicata`
  - **Commit:**

- [ ] **T-014** — Pendência: reembolsável > 500,00 vira `pendente`; resumo
  com `total_pendente` e `pendentes`.
  - **Atende:** RN-015, RN-012, AMB-025, B-24, B-25
  - **Aceite:** `test_rn_015_acima_de_500_fica_pendente`, `test_b_24_exatamente_500_aprovado`,
    `test_rn_012_pendente_fora_do_total_reembolsavel`
  - **Commit:**

- [ ] **T-015** — CLI com `--politica` e `--cambio` opcionais; campos novos na
  saída; ponta a ponta E-02 e E-03; E-01 inalterado; README e CLAUDE.md.
  - **Atende:** spec 4.1/4.2 [v4], 9 (critérios [v4]), E-02, E-03
  - **Aceite:** `test_e_02_envelope_comercial_bate_com_a_spec`, `test_e_03_envelope_cc_desconhecido_bate_com_a_spec`,
    `test_e_01_exemplo_oficial_bate_com_a_spec` (continua passando)
  - **Commit:**

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
| RN-011 | T-009 | `test_rn_011_hospedagem_e_uma_diaria` |
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
| RN-013, AMB-016..018, 024, 027, 028 | T-012 | `test_rn_013_*` |
| RN-014, AMB-019..023, 026 | T-013 | `test_rn_014_*`, `test_amb_022_*`, `test_b_2N_*` |
| RN-015, AMB-025 | T-014 | `test_rn_015_*`, `test_b_24_*` |
| E-02, E-03 | T-015 | `test_e_02_*`, `test_e_03_*` |
| E-01 | T-011 | `test_e_01_exemplo_oficial_bate_com_a_spec` |
