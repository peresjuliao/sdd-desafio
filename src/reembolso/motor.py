"""Motor de cálculo: função pura, ordem de regras da spec seção 8."""
from dataclasses import dataclass

from .entrada import Despesa, Pedido


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
    estado = {"vistos": set()}   # chaves de duplicata já avaliadas (RN-007)
    avaliacoes = [_avaliar(d, pedido, politica, estado) for d in pedido.despesas]
    return Resultado(politica["versao"], pedido, avaliacoes)


def _chave_duplicata(d: Despesa):
    return (d.data, d.categoria, d.fornecedor_norm, d.valor)


def _avaliar(d: Despesa, pedido: Pedido, politica: dict, estado: dict) -> Avaliacao:
    # ordem da spec seção 8: a primeira regra que recusa vence
    if d.valor <= 0:                                                         # RN-009
        return _recusa(d, "valor_invalido", f"valor {reais(d.valor)} nao e uma despesa")
    if not (pedido.inicio <= d.data <= pedido.fim):                          # RN-006
        return _recusa(d, "fora_da_competencia",
                       f"data {d.data} fora do periodo {pedido.inicio} a {pedido.fim}")
    if d.categoria not in politica["limites"]:                               # RN-008
        return _recusa(d, "categoria_nao_coberta", f"categoria '{d.categoria}' nao esta na politica")
    chave = _chave_duplicata(d)                                              # RN-007
    if chave in estado["vistos"]:
        return _recusa(d, "duplicata",
                       f"repete item anterior de {d.data}, {d.categoria}, {d.fornecedor}, {reais(d.valor)}")
    estado["vistos"].add(chave)
    piso = politica["nota_fiscal_obrigatoria_acima_de"]                      # RN-003
    if d.valor > piso and not d.tem_nota_fiscal:
        return _recusa(d, "sem_nota_fiscal", f"valor {reais(d.valor)} acima de {reais(piso)} exige nota fiscal")
    return Avaliacao(d, d.valor, "aprovado", "dentro_do_limite", "")
