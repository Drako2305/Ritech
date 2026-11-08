"""Orquesta la administración de usuarios: cada operación exige que quien la
pide (`id_usuario_solicitante`) tenga rol ADMINISTRADOR.

Nota de seguridad: como el login no emite token de sesión, esta verificación
se hace consultando el rol guardado en la base para ese id — no es a prueba
de suplantación (cualquiera puede mandar el id que quiera), pero evita que
un ejecutar sin más un usuario común dispare estas operaciones por error o
sin saber que existen.
"""

from dominio.excepciones import PermisoDenegadoError, UsuarioNoEncontradoError
from dominio.usuario import RolUsuario, Usuario
from servicios.repositorio_usuarios import RepositorioUsuarios


class ServicioAdministracionUsuarios:
    def __init__(self, repositorio: RepositorioUsuarios):
        self._repositorio = repositorio

    def listar_usuarios(self, id_usuario_solicitante: str) -> list[Usuario]:
        self._verificar_administrador(id_usuario_solicitante)
        return self._repositorio.listar_todos()

    def obtener_usuario(self, id_usuario_solicitante: str, id_usuario_objetivo: str) -> Usuario:
        self._verificar_administrador(id_usuario_solicitante)
        usuario = self._repositorio.buscar_por_id(id_usuario_objetivo)
        if usuario is None:
            raise UsuarioNoEncontradoError(id_usuario_objetivo)
        return usuario

    def eliminar_usuario(self, id_usuario_solicitante: str, id_usuario_objetivo: str) -> None:
        self._verificar_administrador(id_usuario_solicitante)
        self._repositorio.eliminar(id_usuario_objetivo)

    def cambiar_rol(
        self, id_usuario_solicitante: str, id_usuario_objetivo: str, nuevo_rol: RolUsuario
    ) -> Usuario:
        self._verificar_administrador(id_usuario_solicitante)
        self._repositorio.actualizar_rol(id_usuario_objetivo, nuevo_rol)
        return self._repositorio.buscar_por_id(id_usuario_objetivo)

    def _verificar_administrador(self, id_usuario_solicitante: str) -> None:
        solicitante = self._repositorio.buscar_por_id(id_usuario_solicitante)
        if solicitante is None or solicitante.rol != RolUsuario.ADMINISTRADOR:
            raise PermisoDenegadoError()
