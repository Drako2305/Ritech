from decimal import Decimal

import pytest

from dominio.estadisticas import Estadisticas
from dominio.excepciones import PermisoDenegadoError
from dominio.usuario import RolUsuario, Usuario
from servicios.servicio_dashboard import ServicioDashboard
from tests.dobles import RepositorioEstadisticasFalso, RepositorioUsuariosFalso


def _crear_usuario(repositorio: RepositorioUsuariosFalso, rol: RolUsuario, correo: str) -> str:
    usuario = Usuario(nombre="Test", correo=correo, rol=rol, contrasena_hash="hash")
    repositorio.crear(usuario)
    return usuario.id_usuario


def test_un_administrador_puede_ver_las_estadisticas():
    repositorio_usuarios = RepositorioUsuariosFalso()
    id_admin = _crear_usuario(repositorio_usuarios, RolUsuario.ADMINISTRADOR, "admin@ritechqa.co")
    estadisticas_esperadas = Estadisticas(
        total_usuarios=3, total_simulaciones=5,
        capital_total_simulado=Decimal("500000"), rendimiento_promedio=Decimal("1.5"),
    )
    servicio = ServicioDashboard(
        repositorio_usuarios=repositorio_usuarios,
        repositorio_estadisticas=RepositorioEstadisticasFalso(estadisticas_esperadas),
    )

    estadisticas = servicio.obtener_estadisticas(id_admin)

    assert estadisticas == estadisticas_esperadas


def test_un_inversionista_no_puede_ver_las_estadisticas():
    repositorio_usuarios = RepositorioUsuariosFalso()
    id_inversionista = _crear_usuario(
        repositorio_usuarios, RolUsuario.INVERSIONISTA, "inversionista@ritechqa.co"
    )
    servicio = ServicioDashboard(
        repositorio_usuarios=repositorio_usuarios,
        repositorio_estadisticas=RepositorioEstadisticasFalso(),
    )

    with pytest.raises(PermisoDenegadoError):
        servicio.obtener_estadisticas(id_inversionista)


def test_un_id_solicitante_inexistente_no_tiene_permisos():
    servicio = ServicioDashboard(
        repositorio_usuarios=RepositorioUsuariosFalso(),
        repositorio_estadisticas=RepositorioEstadisticasFalso(),
    )

    with pytest.raises(PermisoDenegadoError):
        servicio.obtener_estadisticas("no-existe")
