"""Entidad Alerta: comentario/noticia generado a partir de una simulación
(tabla noticias_alertas)."""

from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass(frozen=True)
class Alerta:
    id_simulacion: str
    titulo: str
    contenido: str
    generado_por_ia: bool = True
    id_alerta: str = field(default_factory=lambda: str(uuid.uuid4()))
    creado_en: datetime = field(default_factory=datetime.now)
