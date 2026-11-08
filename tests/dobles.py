"""Dobles de prueba (stubs/fakes) compartidos entre módulos de test."""

from dataclasses import replace
from decimal import Decimal

from dominio.alerta import Alerta
from dominio.estadisticas import Estadisticas
from dominio.excepciones import (
    CorreoDuplicadoError,
    ErrorConsultaNoticias,
    ErrorGeneracionAlerta,
    UsuarioConSimulacionesError,
    UsuarioNoEncontradoError,
)
from dominio.noticia import Noticia
from dominio.simulacion import Simulacion
from dominio.usuario import RolUsuario, Usuario
from servicios.generador_alerta import GeneradorAlerta
from servicios.generador_variacion import GeneradorVariacionNasdaq
from servicios.proveedor_noticias import ProveedorNoticiasFinancieras
from servicios.repositorio_alertas import RepositorioAlertas
from servicios.repositorio_estadisticas import RepositorioEstadisticas
from servicios.repositorio_simulaciones import RepositorioSimulaciones
from servicios.repositorio_usuarios import RepositorioUsuarios


class GeneradorVariacionFalso(GeneradorVariacionNasdaq):
    def __init__(self, variacion: Decimal):
        self._variacion = variacion

    def generar_variacion(self) -> Decimal:
        return self._variacion


class RepositorioSimulacionesFalso(RepositorioSimulaciones):
    """Guarda en memoria; simula el rechazo por llave foránea si el
    id_usuario no está en `usuarios_validos`, igual que haría Postgres.
    """

    def __init__(self, usuarios_validos: set[str] | None = None):
        self.simulaciones_guardadas: list[Simulacion] = []
        self._usuarios_validos = usuarios_validos

    def guardar(self, simulacion: Simulacion) -> None:
        if (
            self._usuarios_validos is not None
            and simulacion.id_usuario not in self._usuarios_validos
        ):
            raise UsuarioNoEncontradoError(simulacion.id_usuario)
        self.simulaciones_guardadas.append(simulacion)

    def listar_por_usuario(self, id_usuario: str) -> list[Simulacion]:
        return [s for s in self.simulaciones_guardadas if s.id_usuario == id_usuario]


class RepositorioUsuariosFalso(RepositorioUsuarios):
    """Guarda en memoria; simula el rechazo por correo duplicado (UNIQUE) y,
    para `eliminar`, el rechazo por llave foránea si el id está en
    `ids_con_simulaciones` (igual que haría Postgres).
    """

    def __init__(self, ids_con_simulaciones: set[str] | None = None):
        self.usuarios_creados: list[Usuario] = []
        self._ids_con_simulaciones = ids_con_simulaciones or set()

    def crear(self, usuario: Usuario) -> None:
        if any(u.correo == usuario.correo for u in self.usuarios_creados):
            raise CorreoDuplicadoError(usuario.correo)
        self.usuarios_creados.append(usuario)

    def buscar_por_correo(self, correo: str) -> Usuario | None:
        return next((u for u in self.usuarios_creados if u.correo == correo), None)

    def buscar_por_id(self, id_usuario: str) -> Usuario | None:
        return next((u for u in self.usuarios_creados if u.id_usuario == id_usuario), None)

    def listar_todos(self) -> list[Usuario]:
        return list(self.usuarios_creados)

    def eliminar(self, id_usuario: str) -> None:
        if id_usuario in self._ids_con_simulaciones:
            raise UsuarioConSimulacionesError(id_usuario)
        usuario = self.buscar_por_id(id_usuario)
        if usuario is None:
            raise UsuarioNoEncontradoError(id_usuario)
        self.usuarios_creados.remove(usuario)

    def actualizar_rol(self, id_usuario: str, nuevo_rol: RolUsuario) -> None:
        usuario = self.buscar_por_id(id_usuario)
        if usuario is None:
            raise UsuarioNoEncontradoError(id_usuario)
        indice = self.usuarios_creados.index(usuario)
        self.usuarios_creados[indice] = replace(usuario, rol=nuevo_rol)


class GeneradorAlertaFalso(GeneradorAlerta):
    """Si `debe_fallar` es True, simula que la IA no pudo generar la alerta."""

    def __init__(self, titulo: str = "Título falso", contenido: str = "Contenido falso",
                 debe_fallar: bool = False):
        self._titulo = titulo
        self._contenido = contenido
        self._debe_fallar = debe_fallar

    def generar(self, simulacion: Simulacion) -> tuple[str, str]:
        if self._debe_fallar:
            raise ErrorGeneracionAlerta("Fallo simulado de generación de alerta.")
        return self._titulo, self._contenido


class RepositorioAlertasFalso(RepositorioAlertas):
    def __init__(self):
        self.alertas_guardadas: list[Alerta] = []

    def guardar(self, alerta: Alerta) -> None:
        self.alertas_guardadas.append(alerta)

    def listar_por_usuario(self, id_usuario: str) -> list[Alerta]:
        # En la implementación real esto se resuelve con un JOIN a
        # simulaciones; aquí basta con simular la lista ya filtrada.
        return list(self.alertas_guardadas)


class ProveedorNoticiasFalso(ProveedorNoticiasFinancieras):
    """Si `debe_fallar` es True, simula que la consulta de noticias falló."""

    def __init__(self, noticias: list[Noticia] | None = None, debe_fallar: bool = False):
        self._noticias = noticias if noticias is not None else [
            Noticia(titulo="Noticia falsa", resumen="Resumen falso")
        ]
        self._debe_fallar = debe_fallar

    def obtener_noticias(self, limite: int = 5) -> list[Noticia]:
        if self._debe_fallar:
            raise ErrorConsultaNoticias("Fallo simulado al consultar noticias.")
        return self._noticias[:limite]


class RepositorioEstadisticasFalso(RepositorioEstadisticas):
    def __init__(self, estadisticas: Estadisticas | None = None):
        self._estadisticas = estadisticas or Estadisticas(
            total_usuarios=0, total_simulaciones=0,
            capital_total_simulado=Decimal("0"), rendimiento_promedio=Decimal("0"),
        )

    def obtener(self) -> Estadisticas:
        return self._estadisticas
