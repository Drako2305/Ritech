"""Orquesta registro e inicio de sesión, igual que MotorSimulacion orquesta
la simulación: valida reglas de negocio y delega el hash/verificación y el
almacenamiento a colaboradores inyectados (fácil de testear con dobles)."""

from dominio.excepciones import CredencialesInvalidasError
from dominio.usuario import RolUsuario, Usuario
from servicios.autenticador import Autenticador
from servicios.repositorio_usuarios import RepositorioUsuarios


class ServicioAutenticacion:
    def __init__(self, repositorio: RepositorioUsuarios, autenticador: Autenticador | None = None):
        self._repositorio = repositorio
        self._autenticador = autenticador or Autenticador()

    def registrar(self, nombre: str, correo: str, rol: RolUsuario, contrasena: str) -> Usuario:
        contrasena_hash = self._autenticador.hashear(contrasena)
        usuario = Usuario(nombre=nombre, correo=correo, rol=rol, contrasena_hash=contrasena_hash)
        self._repositorio.crear(usuario)
        return usuario

    def iniciar_sesion(self, correo: str, contrasena: str) -> Usuario:
        usuario = self._repositorio.buscar_por_correo(correo)
        if usuario is None or not self._autenticador.verificar(contrasena, usuario.contrasena_hash):
            raise CredencialesInvalidasError()
        return usuario
