"""Agregados globales para el dashboard (solo lectura, no se persiste)."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Estadisticas:
    total_usuarios: int
    total_simulaciones: int
    capital_total_simulado: Decimal
    rendimiento_promedio: Decimal
