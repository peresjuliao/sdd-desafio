"""Leitura e validação da entrada (spec 4.1). Única peça que conhece o formato do JSON."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import json


class EntradaInvalida(Exception):
    pass


@dataclass(frozen=True)
class Despesa:
    id: str
    data: date
    categoria: str          # normalizada (RN-010)
    descricao: str
    fornecedor: str         # original, para a saída
    valor: int              # centavos (RN-010)
    tem_nota_fiscal: bool

    @property
    def fornecedor_norm(self) -> str:
        return normalizar(self.fornecedor)


@dataclass(frozen=True)
class Pedido:
    colaborador: dict
    periodo: dict
    inicio: date
    fim: date
    despesas: list


def normalizar(texto) -> str:
    return str(texto).strip().lower()


def centavos(valor) -> int:
    """RN-010: arredonda a 2 casas, meio para cima. Nunca Decimal(float)."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float, str)):
        raise EntradaInvalida(f"valor nao numerico: {valor!r}")
    try:
        return int(Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100)
    except InvalidOperation:
        raise EntradaInvalida(f"valor nao numerico: {valor!r}")


def _data(texto, campo) -> date:
    try:
        return date.fromisoformat(str(texto))
    except (TypeError, ValueError):
        raise EntradaInvalida(f"{campo}: data ilegivel {texto!r}")


def _obrigatorio(obj, campo, contexto):
    if not isinstance(obj, dict) or campo not in obj or obj[campo] is None:
        raise EntradaInvalida(f"{contexto}: campo obrigatorio ausente: {campo}")
    return obj[campo]


def montar_pedido(dados) -> Pedido:
    colaborador = _obrigatorio(dados, "colaborador", "raiz")
    _obrigatorio(colaborador, "id", "colaborador")
    periodo = _obrigatorio(dados, "periodo", "raiz")
    inicio = _data(_obrigatorio(periodo, "inicio", "periodo"), "periodo.inicio")
    fim = _data(_obrigatorio(periodo, "fim", "periodo"), "periodo.fim")
    lista = _obrigatorio(dados, "despesas", "raiz")
    if not isinstance(lista, list):
        raise EntradaInvalida("despesas: deve ser uma lista")
    despesas = []
    for i, d in enumerate(lista):
        ctx = f"despesas[{i}]"
        despesas.append(Despesa(
            id=str(_obrigatorio(d, "id", ctx)),
            data=_data(_obrigatorio(d, "data", ctx), f"{ctx}.data"),
            categoria=normalizar(_obrigatorio(d, "categoria", ctx)),
            descricao=str(d.get("descricao", "")),
            fornecedor=str(d.get("fornecedor", "")),
            valor=centavos(_obrigatorio(d, "valor", ctx)),
            tem_nota_fiscal=bool(d.get("tem_nota_fiscal", False)),
        ))
    return Pedido(colaborador=dict(colaborador), periodo=dict(periodo),
                  inicio=inicio, fim=fim, despesas=despesas)


def ler_pedido(caminho) -> Pedido:
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
    except OSError as e:
        raise EntradaInvalida(f"nao foi possivel ler {caminho}: {e}")
    except json.JSONDecodeError as e:
        raise EntradaInvalida(f"JSON invalido em {caminho}: {e}")
    return montar_pedido(dados)
