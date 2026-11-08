"""Esquemas Pydantic: forma de las peticiones y respuestas de la API."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from dominio.usuario import RolUsuario


class SolicitudSimulacion(BaseModel):
    id_usuario: str
    capital_inicial: Decimal = Field(gt=0)
    # Si se envía, se simula ese escenario en vez de la variación real del día.
    variacion_nasdaq: Decimal | None = Field(default=None, ge=-50, le=50)


class RespuestaAlerta(BaseModel):
    id_alerta: str
    titulo: str
    contenido: str


class RespuestaSimulacion(BaseModel):
    id_simulacion: str
    id_usuario: str
    capital_inicial: Decimal
    variacion_nasdaq: Decimal
    rendimiento_porcentaje: Decimal
    monto_final: Decimal
    fecha_simulacion: datetime
    alerta: RespuestaAlerta | None = None


class SolicitudRegistro(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    correo: EmailStr
    rol: RolUsuario
    contrasena: str = Field(min_length=6, max_length=72)  # 72: límite de bcrypt


class SolicitudLogin(BaseModel):
    correo: EmailStr
    contrasena: str


class RespuestaUsuario(BaseModel):
    id_usuario: str
    nombre: str
    correo: str
    rol: RolUsuario


class SolicitudCambioRol(BaseModel):
    nuevo_rol: RolUsuario


class RespuestaEstadisticas(BaseModel):
    total_usuarios: int
    total_simulaciones: int
    capital_total_simulado: Decimal
    rendimiento_promedio: Decimal


class RespuestaOperacionTI(BaseModel):
    estado_api: str
    estado_base_datos: str
    fuente_mercado: str
    estado_alertas: str
    total_usuarios: int
    total_simulaciones: int
    capital_total_simulado: Decimal
    rendimiento_promedio: Decimal


class RespuestaPuntoMercado(BaseModel):
    fecha: datetime
    cierre: Decimal


class RespuestaMercado(BaseModel):
    simbolo: str
    nombre: str
    precio: Decimal
    cierre_anterior: Decimal
    variacion_absoluta: Decimal
    variacion_porcentaje: Decimal
    moneda: str
    maximo_dia: Decimal | None = None
    minimo_dia: Decimal | None = None
    actualizado_en: datetime
    historial: list[RespuestaPuntoMercado] = []
