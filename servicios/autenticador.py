"""Hashing y verificación de contraseñas con bcrypt.

Aísla la librería concreta (bcrypt) del resto del sistema: si mañana se
cambia de algoritmo, solo se toca esta clase.
"""

import bcrypt


class Autenticador:
    def hashear(self, contrasena: str) -> str:
        return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()

    def verificar(self, contrasena: str, contrasena_hash: str) -> bool:
        return bcrypt.checkpw(contrasena.encode(), contrasena_hash.encode())
