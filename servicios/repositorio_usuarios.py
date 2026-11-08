"""Persistencia de usuarios (mismo patrón que RepositorioSimulaciones)."""

from abc import ABC, abstractmethod
import sqlite3

import psycopg
from psycopg import errors as errores_psycopg
from psycopg.rows import dict_row

from dominio.excepciones import (
    CorreoDuplicadoError,
    IdentificadorInvalidoError,
    UsuarioConSimulacionesError,
    UsuarioNoEncontradoError,
)
from dominio.usuario import RolUsuario, Usuario
from servicios.sqlite_compat import abrir_conexion, es_sqlite


class RepositorioUsuarios(ABC):
    """Contrato: cualquier forma de guardar/consultar usuarios debe cumplirlo."""

    @abstractmethod
    def crear(self, usuario: Usuario) -> None:
        raise NotImplementedError

    @abstractmethod
    def buscar_por_correo(self, correo: str) -> Usuario | None:
        raise NotImplementedError

    @abstractmethod
    def buscar_por_id(self, id_usuario: str) -> Usuario | None:
        raise NotImplementedError

    @abstractmethod
    def listar_todos(self) -> list[Usuario]:
        raise NotImplementedError

    @abstractmethod
    def eliminar(self, id_usuario: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def actualizar_rol(self, id_usuario: str, nuevo_rol: RolUsuario) -> None:
        raise NotImplementedError


class RepositorioUsuariosPostgres(RepositorioUsuarios):
    """Guarda/consulta usuarios en la tabla `usuarios` (ver db/schema.sql)."""

    def __init__(self, cadena_conexion: str):
        self._cadena_conexion = cadena_conexion

    def crear(self, usuario: Usuario) -> None:
        if es_sqlite(self._cadena_conexion):
            with abrir_conexion(self._cadena_conexion) as conexion:
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
                try:
                    conexion.execute(
                        "INSERT INTO usuarios (id, nombre, correo, rol, contrasena_hash) VALUES (?, ?, ?, ?, ?)",
                        (
                            usuario.id_usuario,
                            usuario.nombre,
                            usuario.correo,
                            usuario.rol.value,
                            usuario.contrasena_hash,
                        ),
                    )
                except sqlite3.IntegrityError as error:
                    raise CorreoDuplicadoError(usuario.correo) from error
            return

        try:
            with psycopg.connect(self._cadena_conexion) as conexion:
                conexion.execute(
                    """
                    INSERT INTO usuarios (id, nombre, correo, rol, contrasena_hash)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        usuario.id_usuario,
                        usuario.nombre,
                        usuario.correo,
                        usuario.rol.value,
                        usuario.contrasena_hash,
                    ),
                )
        except errores_psycopg.UniqueViolation as error:
            raise CorreoDuplicadoError(usuario.correo) from error

    def buscar_por_correo(self, correo: str) -> Usuario | None:
        if es_sqlite(self._cadena_conexion):
            with abrir_conexion(self._cadena_conexion) as conexion:
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
                fila = conexion.execute(
                    "SELECT id, nombre, correo, rol, contrasena_hash FROM usuarios WHERE correo = ?",
                    (correo,),
                ).fetchone()
            return self._fila_a_usuario(fila)

        with psycopg.connect(self._cadena_conexion) as conexion:
            cursor = conexion.cursor(row_factory=dict_row)
            cursor.execute(
                """
                SELECT id, nombre, correo, rol, contrasena_hash
                FROM usuarios WHERE correo = %s
                """,
                (correo,),
            )
            return self._fila_a_usuario(cursor.fetchone())

    def buscar_por_id(self, id_usuario: str) -> Usuario | None:
        if es_sqlite(self._cadena_conexion):
            with abrir_conexion(self._cadena_conexion) as conexion:
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
                fila = conexion.execute(
                    "SELECT id, nombre, correo, rol, contrasena_hash FROM usuarios WHERE id = ?",
                    (id_usuario,),
                ).fetchone()
            return self._fila_a_usuario(fila)

        try:
            with psycopg.connect(self._cadena_conexion) as conexion:
                cursor = conexion.cursor(row_factory=dict_row)
                cursor.execute(
                    """
                    SELECT id, nombre, correo, rol, contrasena_hash
                    FROM usuarios WHERE id = %s
                    """,
                    (id_usuario,),
                )
                return self._fila_a_usuario(cursor.fetchone())
        except errores_psycopg.InvalidTextRepresentation as error:
            raise IdentificadorInvalidoError(id_usuario) from error

    def listar_todos(self) -> list[Usuario]:
        if es_sqlite(self._cadena_conexion):
            with abrir_conexion(self._cadena_conexion) as conexion:
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
                filas = conexion.execute(
                    "SELECT id, nombre, correo, rol, contrasena_hash FROM usuarios ORDER BY nombre"
                ).fetchall()
            return [self._fila_a_usuario(fila) for fila in filas]

        with psycopg.connect(self._cadena_conexion) as conexion:
            cursor = conexion.cursor(row_factory=dict_row)
            cursor.execute(
                "SELECT id, nombre, correo, rol, contrasena_hash FROM usuarios ORDER BY nombre"
            )
            return [self._fila_a_usuario(fila) for fila in cursor.fetchall()]

    def eliminar(self, id_usuario: str) -> None:
        if es_sqlite(self._cadena_conexion):
            with abrir_conexion(self._cadena_conexion) as conexion:
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
                cursor = conexion.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
                if cursor.rowcount == 0:
                    raise UsuarioNoEncontradoError(id_usuario)
                return

        try:
            with psycopg.connect(self._cadena_conexion) as conexion:
                cursor = conexion.execute("DELETE FROM usuarios WHERE id = %s", (id_usuario,))
                if cursor.rowcount == 0:
                    raise UsuarioNoEncontradoError(id_usuario)
        except errores_psycopg.ForeignKeyViolation as error:
            raise UsuarioConSimulacionesError(id_usuario) from error
        except errores_psycopg.InvalidTextRepresentation as error:
            raise IdentificadorInvalidoError(id_usuario) from error

    def actualizar_rol(self, id_usuario: str, nuevo_rol: RolUsuario) -> None:
        if es_sqlite(self._cadena_conexion):
            with abrir_conexion(self._cadena_conexion) as conexion:
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
                cursor = conexion.execute(
                    "UPDATE usuarios SET rol = ? WHERE id = ?",
                    (nuevo_rol.value, id_usuario),
                )
                if cursor.rowcount == 0:
                    raise UsuarioNoEncontradoError(id_usuario)
                return

        try:
            with psycopg.connect(self._cadena_conexion) as conexion:
                cursor = conexion.execute(
                    "UPDATE usuarios SET rol = %s WHERE id = %s", (nuevo_rol.value, id_usuario)
                )
                if cursor.rowcount == 0:
                    raise UsuarioNoEncontradoError(id_usuario)
        except errores_psycopg.InvalidTextRepresentation as error:
            raise IdentificadorInvalidoError(id_usuario) from error

    @staticmethod
    def _fila_a_usuario(fila: dict | None) -> Usuario | None:
        # dict_row (no class_row) porque Postgres devuelve `id` como UUID;
        # hay que forzarlo a str para respetar el tipo declarado en Usuario.
        if fila is None:
            return None
        return Usuario(
            id_usuario=str(fila["id"]),
            nombre=fila["nombre"],
            correo=fila["correo"],
            rol=RolUsuario(fila["rol"]),
            contrasena_hash=fila["contrasena_hash"],
        )
