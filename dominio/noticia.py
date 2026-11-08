"""Una noticia financiera externa, insumo para que la IA redacte la alerta
(no se persiste; es un dato de paso entre ProveedorNoticiasFinancieras y
GeneradorAlerta)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Noticia:
    titulo: str
    resumen: str
