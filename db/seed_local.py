"""Crea las cuentas de demo en la base SQLite local, sin duplicarlas."""

import sqlite3
from pathlib import Path


BASE_DATOS = Path(__file__).with_name("ritech.db")
HASH_CONTRASENA_DEMO = "$2b$12$EkxtauWYDQ27yi05ceGU1eH/qEm8KZijj2fHyTG3xz3vjMxKHFn0q"
CUENTAS = (
    ("11111111-1111-1111-1111-111111111111", "Laura Benavides", "inversionista@ritech.com", "INVERSIONISTA"),
    ("22222222-2222-2222-2222-222222222222", "Carlos Ruiz", "gestor@ritech.com", "GESTOR_TI"),
    ("33333333-3333-3333-3333-333333333333", "Administrador RiTech", "admin@ritech.com", "ADMINISTRADOR"),
)


with sqlite3.connect(BASE_DATOS) as conexion:
    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL UNIQUE,
            rol TEXT NOT NULL CHECK (rol IN ('INVERSIONISTA', 'GESTOR_TI', 'ADMINISTRADOR')),
            contrasena_hash TEXT NOT NULL,
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conexion.executemany(
        """
        INSERT INTO usuarios (id, nombre, correo, rol, contrasena_hash)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(correo) DO NOTHING
        """,
        [(*cuenta, HASH_CONTRASENA_DEMO) for cuenta in CUENTAS],
    )

print("Cuentas de demo listas en db/ritech.db; cambia la contraseña antes de desplegar.")
