"""Fábricas de dependencias de la API (inyección de dependencias).

Al pasar por Depends(), los tests pueden reemplazarlas por versiones falsas
sin tocar main.py.
"""

import os
from functools import lru_cache
from pathlib import Path

from fastapi import Depends

from servicios.autenticador import Autenticador
from servicios.generador_alerta import (
    GeneradorAlertaConRespaldo,
    GeneradorAlertaGemini,
    GeneradorAlertaLocal,
)
from servicios.generador_variacion import (
    GeneradorVariacionAlphaVantage,
    GeneradorVariacionConRespaldo,
    GeneradorVariacionYahoo,
)
from servicios.motor_simulacion import MotorSimulacion
from servicios.proveedor_mercado import ProveedorMercadoYahoo
from servicios.proveedor_noticias import ProveedorNoticiasAlphaVantage
from servicios.repositorio_alertas import RepositorioAlertasPostgres
from servicios.repositorio_estadisticas import RepositorioEstadisticasPostgres
from servicios.repositorio_simulaciones import RepositorioSimulacionesPostgres
from servicios.repositorio_usuarios import RepositorioUsuariosPostgres
from servicios.servicio_administracion_usuarios import ServicioAdministracionUsuarios
from servicios.servicio_alertas import ServicioAlertas
from servicios.servicio_autorizacion_roles import ServicioAutorizacionRoles
from servicios.servicio_autenticacion import ServicioAutenticacion
from servicios.servicio_dashboard import ServicioDashboard
from servicios.servicio_operacion_ti import ServicioOperacionTI


def _cadena_conexion() -> str:
    valor = os.environ.get("DATABASE_URL")
    if valor:
        return valor

    base = Path(__file__).resolve().parent.parent
    return str(base / "db" / "ritech.db")


@lru_cache
def obtener_motor_simulacion() -> MotorSimulacion:
    if os.environ.get("ALPHAVANTAGE_API_KEY"):
        generador = GeneradorVariacionConRespaldo(
            primario=GeneradorVariacionAlphaVantage(),
            respaldo=GeneradorVariacionYahoo(),
        )
    else:
        generador = GeneradorVariacionYahoo()
    return MotorSimulacion(generador_variacion=generador)


@lru_cache
def obtener_proveedor_mercado() -> ProveedorMercadoYahoo:
    return ProveedorMercadoYahoo()


@lru_cache
def obtener_repositorio_simulaciones() -> RepositorioSimulacionesPostgres:
    return RepositorioSimulacionesPostgres(_cadena_conexion())


@lru_cache
def obtener_repositorio_usuarios() -> RepositorioUsuariosPostgres:
    return RepositorioUsuariosPostgres(_cadena_conexion())


def obtener_servicio_autenticacion(
    repositorio: RepositorioUsuariosPostgres = Depends(obtener_repositorio_usuarios),
) -> ServicioAutenticacion:
    return ServicioAutenticacion(repositorio=repositorio, autenticador=Autenticador())


def obtener_servicio_autorizacion_roles(
    repositorio: RepositorioUsuariosPostgres = Depends(obtener_repositorio_usuarios),
) -> ServicioAutorizacionRoles:
    return ServicioAutorizacionRoles(repositorio_usuarios=repositorio)


def obtener_servicio_administracion_usuarios(
    repositorio: RepositorioUsuariosPostgres = Depends(obtener_repositorio_usuarios),
) -> ServicioAdministracionUsuarios:
    return ServicioAdministracionUsuarios(repositorio=repositorio)


@lru_cache
def obtener_repositorio_alertas() -> RepositorioAlertasPostgres:
    return RepositorioAlertasPostgres(_cadena_conexion())


def obtener_servicio_alertas(
    repositorio: RepositorioAlertasPostgres = Depends(obtener_repositorio_alertas),
) -> ServicioAlertas:
    generador = GeneradorAlertaConRespaldo(
        primario=GeneradorAlertaGemini(proveedor_noticias=ProveedorNoticiasAlphaVantage()),
        respaldo=GeneradorAlertaLocal(),
    )
    return ServicioAlertas(generador=generador, repositorio=repositorio)


@lru_cache
def obtener_repositorio_estadisticas() -> RepositorioEstadisticasPostgres:
    return RepositorioEstadisticasPostgres(_cadena_conexion())


def obtener_servicio_dashboard(
    repositorio_usuarios: RepositorioUsuariosPostgres = Depends(obtener_repositorio_usuarios),
    repositorio_estadisticas: RepositorioEstadisticasPostgres = Depends(
        obtener_repositorio_estadisticas
    ),
) -> ServicioDashboard:
    return ServicioDashboard(
        repositorio_usuarios=repositorio_usuarios,
        repositorio_estadisticas=repositorio_estadisticas,
    )


def obtener_servicio_operacion_ti(
    repositorio_usuarios: RepositorioUsuariosPostgres = Depends(obtener_repositorio_usuarios),
    repositorio_estadisticas: RepositorioEstadisticasPostgres = Depends(
        obtener_repositorio_estadisticas
    ),
) -> ServicioOperacionTI:
    return ServicioOperacionTI(
        repositorio_usuarios=repositorio_usuarios,
        repositorio_estadisticas=repositorio_estadisticas,
    )
