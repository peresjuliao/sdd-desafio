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
    avaliacoes = [_avaliar(d, pedido, politica) for d in pedido.despesas]
    return Resultado(politica["versao"], pedido, avaliacoes)


def _avaliar(d: Despesa, pedido: Pedido, politica: dict) -> Avaliacao:
    return Avaliacao(d, d.valor, "aprovado", "dentro_do_limite", "")
