"""Entidad Usuario. `contrasena_hash` nunca es la contraseña en texto plano:
la genera Autenticador antes de construir el objeto."""

from dataclasses import dataclass, field
from enum import Enum
import uuid


class RolUsuario(str, Enum):
    INVERSIONISTA = "INVERSIONISTA"
    GESTOR_TI = "GESTOR_TI"
    ADMINISTRADOR = "ADMINISTRADOR"


@dataclass(frozen=True)
class Usuario:
    nombre: str
    correo: str
    rol: RolUsuario
    contrasena_hash: str
    id_usuario: str = field(default_factory=lambda: str(uuid.uuid4()))
