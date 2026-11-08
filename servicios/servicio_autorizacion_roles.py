"""Validación de acceso a funciones de RiTech según el rol guardado."""

from dominio.excepciones import PermisoDenegadoError, UsuarioNoEncontradoError
from dominio.usuario import RolUsuario, Usuario
from servicios.repositorio_usuarios import RepositorioUsuarios


class ServicioAutorizacionRoles:
    def __init__(self, repositorio_usuarios: RepositorioUsuarios):
        self._repositorio_usuarios = repositorio_usuarios

    def exigir_rol(self, id_usuario: str, rol_requerido: RolUsuario) -> Usuario:
        usuario = self._repositorio_usuarios.buscar_por_id(id_usuario)
        if usuario is None:
            raise UsuarioNoEncontradoError(id_usuario)
        if usuario.rol != rol_requerido:
            raise PermisoDenegadoError()
        return usuario
