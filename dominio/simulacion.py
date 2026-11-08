"""Entidad Simulacion: el resultado ya calculado de una simulación de inversión.

Es inmutable (frozen=True) porque representa un cálculo que ya ocurrió,
no algo que deba modificarse después.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
import uuid


@dataclass(frozen=True)
class Simulacion:
    id_usuario: str
    capital_inicial: Decimal
    variacion_nasdaq: Decimal
    rendimiento_porcentaje: Decimal
    monto_final: Decimal
    id_simulacion: str = field(default_factory=lambda: str(uuid.uuid4()))
    fecha_simulacion: datetime = field(default_factory=datetime.now)
