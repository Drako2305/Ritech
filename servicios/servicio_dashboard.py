"""Orquesta el dashboard: solo ADMINISTRADOR puede ver los agregados
globales (misma verificación por parámetro que ServicioAdministracionUsuarios,
ver ese archivo para la nota de seguridad sobre no tener token de sesión)."""

from dominio.estadisticas import Estadisticas
from dominio.excepciones import PermisoDenegadoError
from dominio.usuario import RolUsuario
from servicios.repositorio_estadisticas import RepositorioEstadisticas
from servicios.repositorio_usuarios import RepositorioUsuarios


class ServicioDashboard:
    def __init__(
        self, repositorio_usuarios: RepositorioUsuarios,
        repositorio_estadisticas: RepositorioEstadisticas,
    ):
        self._repositorio_usuarios = repositorio_usuarios
        self._repositorio_estadisticas = repositorio_estadisticas

    def obtener_estadisticas(self, id_usuario_solicitante: str) -> Estadisticas:
        self._verificar_administrador(id_usuario_solicitante)
        return self._repositorio_estadisticas.obtener()

    def _verificar_administrador(self, id_usuario_solicitante: str) -> None:
        solicitante = self._repositorio_usuarios.buscar_por_id(id_usuario_solicitante)
        if solicitante is None or solicitante.rol != RolUsuario.ADMINISTRADOR:
            raise PermisoDenegadoError()
