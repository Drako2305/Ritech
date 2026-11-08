"""Consulta de estado operativo exclusiva para el rol Gestor TI."""

import os

from dominio.excepciones import PermisoDenegadoError
from dominio.operacion_ti import OperacionTI
from dominio.usuario import RolUsuario
from servicios.repositorio_estadisticas import RepositorioEstadisticas
from servicios.repositorio_usuarios import RepositorioUsuarios


class ServicioOperacionTI:
    def __init__(
        self,
        repositorio_usuarios: RepositorioUsuarios,
        repositorio_estadisticas: RepositorioEstadisticas,
    ):
        self._repositorio_usuarios = repositorio_usuarios
        self._repositorio_estadisticas = repositorio_estadisticas

    def obtener_estado(self, id_usuario_solicitante: str) -> OperacionTI:
        solicitante = self._repositorio_usuarios.buscar_por_id(id_usuario_solicitante)
        if solicitante is None or solicitante.rol != RolUsuario.GESTOR_TI:
            raise PermisoDenegadoError()

        estadisticas = self._repositorio_estadisticas.obtener()
        fuente_mercado = (
            "Alpha Vantage con respaldo Yahoo Finance (QQQ)"
            if os.environ.get("ALPHAVANTAGE_API_KEY")
            else "Yahoo Finance (QQQ), sin clave"
        )
        estado_alertas = (
            "Gemini configurado (alertas con IA)"
            if os.environ.get("GEMINI_API_KEY")
            else "Alertas locales activas; Gemini sin clave"
        )

        return OperacionTI(
            estado_api="Operativa",
            estado_base_datos="Conectada",
            fuente_mercado=fuente_mercado,
            estado_alertas=estado_alertas,
            total_usuarios=estadisticas.total_usuarios,
            total_simulaciones=estadisticas.total_simulaciones,
            capital_total_simulado=estadisticas.capital_total_simulado,
            rendimiento_promedio=estadisticas.rendimiento_promedio,
        )
