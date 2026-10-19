"""Motor de cálculo: função pura, ordem de regras da spec seção 8."""
from dataclasses import dataclass
from datetime import timedelta

from .entrada import Despesa, Pedido
from .politica import limites_para


@dataclass(frozen=True)
class Avaliacao:
    despesa: Despesa
    reembolsavel: int   # centavos
    status: str         # aprovado | parcial | recusado
    motivo: str
    detalhe: str


@dataclass(frozen=True)
class Resultado:
    politica: str
    pedido: Pedido
    avaliacoes: list

    @property
    def resumo(self) -> dict:  # RN-012
        return {
            "total_solicitado": sum(a.despesa.valor for a in self.avaliacoes),
            "total_reembolsavel": sum(a.reembolsavel for a in self.avaliacoes),
            "aprovados": sum(a.status == "aprovado" for a in self.avaliacoes),
            "parciais": sum(a.status == "parcial" for a in self.avaliacoes),
            "recusados": sum(a.status == "recusado" for a in self.avaliacoes),
        }


def reais(c: int) -> str:
    return f"R$ {c // 100},{c % 100:02d}" if c >= 0 else f"-R$ {-c // 100},{-c % 100:02d}"


def _recusa(d, motivo, detalhe):
    return Avaliacao(d, 0, "recusado", motivo, detalhe)


def calcular(pedido: Pedido, politica: dict) -> Resultado:
    estado = {
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
    return (d.data, d.categoria, d.fornecedor_norm, d.valor)


def _avaliar(d: Despesa, pedido: Pedido, politica: dict, estado: dict) -> Avaliacao:
    # ordem da spec seção 8: a primeira regra que recusa vence
    if d.valor <= 0:                                                         # RN-009
        return _recusa(d, "valor_invalido", f"valor {reais(d.valor)} nao e uma despesa")
    if not (pedido.inicio <= d.data <= pedido.fim):                          # RN-006
        return _recusa(d, "fora_da_competencia",
                       f"data {d.data} fora do periodo {pedido.inicio} a {pedido.fim}")
    if estado["limites"].get(d.categoria, 0) <= 0:                           # RN-008, RN-013
        return _recusa(d, "categoria_nao_coberta",
                       f"categoria '{d.categoria}' nao e reembolsavel para {pedido.colaborador.get('centro_custo') or 'a politica padrao'}")
    chave = _chave_duplicata(d)                                              # RN-007
    if chave in estado["vistos"]:
        return _recusa(d, "duplicata",
                       f"repete item anterior de {d.data}, {d.categoria}, {d.fornecedor}, {reais(d.valor)}")
    estado["vistos"].add(chave)
    piso = politica["nota_fiscal_obrigatoria_acima_de"]                      # RN-003
    if d.valor > piso and not d.tem_nota_fiscal:
        return _recusa(d, "sem_nota_fiscal", f"valor {reais(d.valor)} acima de {reais(piso)} exige nota fiscal")
    # RN-001/RN-002: cota do par (data, categoria), consumida em ordem de entrada
    limite = _limite(d, politica, estado)
    saldo = estado["saldo"].setdefault((d.data, d.categoria), limite)
    pago = min(d.valor, saldo)
    estado["saldo"][(d.data, d.categoria)] = saldo - pago
    viagem = " (em viagem)" if d.data in estado["viagem"] else ""
    detalhe = f"limite de {d.categoria} em {d.data}{viagem} e {reais(limite)}; restavam {reais(saldo)}"
    if pago == d.valor:
        return Avaliacao(d, pago, "aprovado", "dentro_do_limite", detalhe)
    return Avaliacao(d, pago, "parcial" if pago else "recusado", "acima_do_limite_diario", detalhe)


def _limite(d: Despesa, politica: dict, estado: dict) -> int:
    base = estado["limites"][d.categoria]
    if d.data in estado["viagem"]:                                           # RN-004
        return base * (100 + politica["acrescimo_em_viagem_percentual"]) // 100
    return base
