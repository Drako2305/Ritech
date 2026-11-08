"""Estado operativo visible para el rol Gestor TI."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OperacionTI:
    estado_api: str
    estado_base_datos: str
    fuente_mercado: str
    estado_alertas: str
    total_usuarios: int
    total_simulaciones: int
    capital_total_simulado: Decimal
    rendimiento_promedio: Decimal
