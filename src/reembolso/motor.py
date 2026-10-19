"""Motor de cálculo: função pura, ordem de regras da spec seção 8."""
from dataclasses import dataclass
from datetime import timedelta

from .cambio import SEM_CAMBIO, converter, taxa_para
from .entrada import Despesa, Pedido
from .politica import limites_para


@dataclass(frozen=True)
class Avaliacao:
    despesa: Despesa
    reembolsavel: int   # centavos, em reais
    status: str         # aprovado | parcial | recusado | pendente
    motivo: str
    detalhe: str
    valor_brl: int = None   # valor solicitado em reais; None se a conversão falhou (RN-014)
    taxa: object = None     # Decimal usada na conversão; None se falhou


@dataclass(frozen=True)
class Resultado:
    politica: str
    pedido: Pedido
    avaliacoes: list

    @property
    def resumo(self) -> dict:  # RN-012
        return {
            "total_solicitado": sum(a.valor_brl for a in self.avaliacoes if a.valor_brl is not None),
            "total_reembolsavel": sum(a.reembolsavel for a in self.avaliacoes if a.status in ("aprovado", "parcial")),
            "total_pendente": sum(a.reembolsavel for a in self.avaliacoes if a.status == "pendente"),
            "aprovados": sum(a.status == "aprovado" for a in self.avaliacoes),
            "parciais": sum(a.status == "parcial" for a in self.avaliacoes),
            "recusados": sum(a.status == "recusado" for a in self.avaliacoes),
            "pendentes": sum(a.status == "pendente" for a in self.avaliacoes),
        }


def reais(c: int) -> str:
    return f"R$ {c // 100},{c % 100:02d}" if c >= 0 else f"-R$ {-c // 100},{-c % 100:02d}"


def _recusa(d, motivo, detalhe, valor_brl=None, taxa=None):
    return Avaliacao(d, 0, "recusado", motivo, detalhe, valor_brl, taxa)


def calcular(pedido: Pedido, politica: dict, cambio: dict = SEM_CAMBIO) -> Resultado:
    estado = {
        "cambio": cambio,
        "vistos": set(),   # chaves de duplicata já avaliadas (RN-007)
        "saldo": {},       # (data, categoria) -> centavos que restam da cota (RN-001)
        "viagem": _dias_em_viagem(pedido),
        "limites": limites_para(politica, pedido.colaborador.get("centro_custo")),  # RN-013
    }
    avaliacoes = [_avaliar(d, pedido, politica, estado) for d in pedido.despesas]
    return Resultado(politica["versao"], pedido, avaliacoes)


def _dias_em_viagem(pedido: Pedido) -> set:
    """RN-005: hospedagem válida (valor > 0, dentro do período) marca o dia D e D+1,
    mesmo que o item venha a ser recusado por nota ou duplicata."""
    dias = set()
    for d in pedido.despesas:
        if d.categoria == "hospedagem" and d.valor > 0 and pedido.inicio <= d.data <= pedido.fim:
            dias.add(d.data)
            dias.add(d.data + timedelta(days=1))
    return dias


def _chave_duplicata(d: Despesa):
    return (d.data, d.categoria, d.fornecedor_norm, d.moeda, d.valor)   # AMB-023: moeda e valor original


def _avaliar(d: Despesa, pedido: Pedido, politica: dict, estado: dict) -> Avaliacao:
    # Conversão (RN-014) é calculada antes de tudo para que valor_solicitado exista
    # sempre que houver taxa, mesmo em item recusado; o motivo segue a ordem da seção 8.
    taxa = taxa_para(estado["cambio"], d.moeda, d.data)
    valor = converter(d.valor, taxa) if taxa is not None else None   # em reais
    # ordem da spec seção 8: a primeira regra que recusa vence
    if d.valor <= 0:                                                         # RN-009
        return _recusa(d, "valor_invalido", f"valor {d.valor / 100:.2f} {d.moeda} nao e uma despesa", valor, taxa)
    if not (pedido.inicio <= d.data <= pedido.fim):                          # RN-006
        return _recusa(d, "fora_da_competencia",
                       f"data {d.data} fora do periodo {pedido.inicio} a {pedido.fim}", valor, taxa)
    if taxa is None:                                                         # RN-014
        return _recusa(d, "cambio_indisponivel", f"sem taxa de {d.moeda} publicada ate {d.data}")
    conv = f" ({d.valor / 100:.2f} {d.moeda} x {taxa} = {reais(valor)})" if d.moeda != "BRL" else ""
    if estado["limites"].get(d.categoria, 0) <= 0:                           # RN-008, RN-013
        return _recusa(d, "categoria_nao_coberta",
                       f"categoria '{d.categoria}' nao e reembolsavel para {pedido.colaborador.get('centro_custo') or 'a politica padrao'}",
                       valor, taxa)
    chave = _chave_duplicata(d)                                              # RN-007
    if chave in estado["vistos"]:
        return _recusa(d, "duplicata",
                       f"repete item anterior de {d.data}, {d.categoria}, {d.fornecedor}, {d.valor / 100:.2f} {d.moeda}",
                       valor, taxa)
    estado["vistos"].add(chave)
    piso = politica["nota_fiscal_obrigatoria_acima_de"]                      # RN-003
    if valor > piso and not d.tem_nota_fiscal:
        return _recusa(d, "sem_nota_fiscal", f"valor {reais(valor)}{conv} acima de {reais(piso)} exige nota fiscal",
                       valor, taxa)
    # RN-001/RN-002: cota do par (data, categoria), consumida em ordem de entrada
    limite = _limite(d, politica, estado)
    saldo = estado["saldo"].setdefault((d.data, d.categoria), limite)
    pago = min(valor, saldo)
    estado["saldo"][(d.data, d.categoria)] = saldo - pago
    viagem = " (em viagem)" if d.data in estado["viagem"] else ""
    detalhe = f"limite de {d.categoria} em {d.data}{viagem} e {reais(limite)}; restavam {reais(saldo)}{conv}"
    if pago == valor:
        status, motivo = "aprovado", "dentro_do_limite"
    else:
        status, motivo = ("parcial" if pago else "recusado"), "acima_do_limite_diario"
    if pago > politica["pendencia_acima_de"]:                                # RN-015
        status = "pendente"
        detalhe += f"; {reais(pago)} passa de {reais(politica['pendencia_acima_de'])}, aguarda gestor"
    return Avaliacao(d, pago, status, motivo, detalhe, valor, taxa)


def _limite(d: Despesa, politica: dict, estado: dict) -> int:
    base = estado["limites"][d.categoria]
    if d.data in estado["viagem"]:                                           # RN-004
        return base * (100 + politica["acrescimo_em_viagem_percentual"]) // 100
    return base
