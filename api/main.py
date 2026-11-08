"""API REST del backend RiTech: expone el motor de simulación de inversiones."""

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.dependencias import (
    obtener_motor_simulacion,
    obtener_proveedor_mercado,
    obtener_repositorio_alertas,
    obtener_repositorio_simulaciones,
    obtener_servicio_administracion_usuarios,
    obtener_servicio_alertas,
    obtener_servicio_autenticacion,
    obtener_servicio_autorizacion_roles,
    obtener_servicio_dashboard,
    obtener_servicio_operacion_ti,
)
from api.esquemas import (
    RespuestaAlerta,
    RespuestaEstadisticas,
    RespuestaMercado,
    RespuestaOperacionTI,
    RespuestaPuntoMercado,
    RespuestaSimulacion,
    RespuestaUsuario,
    SolicitudCambioRol,
    SolicitudLogin,
    SolicitudRegistro,
    SolicitudSimulacion,
)
from dominio.excepciones import (
    CapitalInsuficienteError,
    CorreoDuplicadoError,
    CredencialesInvalidasError,
    ErrorGeneracionVariacion,
    IdentificadorInvalidoError,
    PermisoDenegadoError,
    UsuarioConSimulacionesError,
    UsuarioNoEncontradoError,
)
from dominio.usuario import RolUsuario
from servicios.motor_simulacion import MotorSimulacion
from servicios.proveedor_mercado import ProveedorMercadoYahoo
from servicios.repositorio_alertas import RepositorioAlertas
from servicios.repositorio_simulaciones import RepositorioSimulaciones
from servicios.servicio_administracion_usuarios import ServicioAdministracionUsuarios
from servicios.servicio_alertas import ServicioAlertas
from servicios.servicio_autorizacion_roles import ServicioAutorizacionRoles
from servicios.servicio_autenticacion import ServicioAutenticacion
from servicios.servicio_dashboard import ServicioDashboard
from servicios.servicio_operacion_ti import ServicioOperacionTI

app = FastAPI(title="RiTech - Motor de Simulación")

# Habilitado para que el panel visual (HTML/JS servido desde otro origen o
# desde disco) pueda llamar a esta API. Para producción se recomienda
# restringir allow_origins al dominio real del frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _exigir_inversionista(
    id_usuario: str,
    autorizacion: ServicioAutorizacionRoles,
) -> None:
    try:
        autorizacion.exigir_rol(id_usuario, RolUsuario.INVERSIONISTA)
    except UsuarioNoEncontradoError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except PermisoDenegadoError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except IdentificadorInvalidoError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/usuarios", response_model=RespuestaUsuario, status_code=201)
def registrar_usuario(
    solicitud: SolicitudRegistro,
    servicio: ServicioAutenticacion = Depends(obtener_servicio_autenticacion),
) -> RespuestaUsuario:
    if solicitud.rol.value != "INVERSIONISTA":
        raise HTTPException(
            status_code=403,
            detail="El registro público solo está disponible para inversionistas.",
        )

    try:
        usuario = servicio.registrar(
            nombre=solicitud.nombre,
            correo=solicitud.correo,
            rol=solicitud.rol,
            contrasena=solicitud.contrasena,
        )
    except CorreoDuplicadoError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    return RespuestaUsuario(**usuario.__dict__)


@app.post("/login", response_model=RespuestaUsuario)
def iniciar_sesion(
    solicitud: SolicitudLogin,
    servicio: ServicioAutenticacion = Depends(obtener_servicio_autenticacion),
) -> RespuestaUsuario:
    try:
        usuario = servicio.iniciar_sesion(correo=solicitud.correo, contrasena=solicitud.contrasena)
    except CredencialesInvalidasError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error

    return RespuestaUsuario(**usuario.__dict__)


@app.get("/mercado/cotizacion", response_model=RespuestaMercado)
def obtener_cotizacion(
    proveedor: ProveedorMercadoYahoo = Depends(obtener_proveedor_mercado),
) -> RespuestaMercado:
    """Cotización en vivo del instrumento que replica el NASDAQ 100 (QQQ)."""
    try:
        cotizacion = proveedor.obtener_cotizacion()
    except ErrorGeneracionVariacion as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return RespuestaMercado(
        simbolo=cotizacion.simbolo,
        nombre=cotizacion.nombre,
        precio=cotizacion.precio,
        cierre_anterior=cotizacion.cierre_anterior,
        variacion_absoluta=cotizacion.variacion_absoluta,
        variacion_porcentaje=cotizacion.variacion_porcentaje,
        moneda=cotizacion.moneda,
        maximo_dia=cotizacion.maximo_dia,
        minimo_dia=cotizacion.minimo_dia,
        actualizado_en=cotizacion.actualizado_en,
        historial=[
            RespuestaPuntoMercado(fecha=punto.fecha, cierre=punto.cierre)
            for punto in cotizacion.historial
        ],
    )


@app.post("/simulaciones", response_model=RespuestaSimulacion, status_code=201)
def crear_simulacion(
    solicitud: SolicitudSimulacion,
    motor: MotorSimulacion = Depends(obtener_motor_simulacion),
    repositorio: RepositorioSimulaciones = Depends(obtener_repositorio_simulaciones),
    servicio_alertas: ServicioAlertas = Depends(obtener_servicio_alertas),
    autorizacion: ServicioAutorizacionRoles = Depends(obtener_servicio_autorizacion_roles),
) -> RespuestaSimulacion:
    _exigir_inversionista(solicitud.id_usuario, autorizacion)

    try:
        simulacion = motor.ejecutar_simulacion(
            id_usuario=solicitud.id_usuario,
            capital_inicial=solicitud.capital_inicial,
            variacion_nasdaq=solicitud.variacion_nasdaq,
        )
    except CapitalInsuficienteError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ErrorGeneracionVariacion as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    try:
        repositorio.guardar(simulacion)
    except UsuarioNoEncontradoError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except IdentificadorInvalidoError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    # La alerta es "best-effort": si Gemini falla, generar_y_guardar retorna
    # None y la simulación (ya guardada) se devuelve igual, sin alerta.
    alerta = servicio_alertas.generar_y_guardar(simulacion)

    respuesta = RespuestaSimulacion(**simulacion.__dict__)
    if alerta is not None:
        respuesta.alerta = RespuestaAlerta(**alerta.__dict__)
    return respuesta


@app.get("/simulaciones/{id_usuario}", response_model=list[RespuestaSimulacion])
def listar_simulaciones(
    id_usuario: str,
    repositorio: RepositorioSimulaciones = Depends(obtener_repositorio_simulaciones),
    autorizacion: ServicioAutorizacionRoles = Depends(obtener_servicio_autorizacion_roles),
) -> list[RespuestaSimulacion]:
    _exigir_inversionista(id_usuario, autorizacion)
    try:
        simulaciones = repositorio.listar_por_usuario(id_usuario)
    except IdentificadorInvalidoError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return [RespuestaSimulacion(**s.__dict__) for s in simulaciones]


# --- Administración de usuarios (solo ADMINISTRADOR) ---------------------
# `id_usuario_solicitante` identifica a quien hace la petición: el backend
# verifica su rol antes de ejecutar la operación (ver ServicioAdministracionUsuarios).

@app.get("/usuarios", response_model=list[RespuestaUsuario])
def listar_usuarios(
    id_usuario_solicitante: str,
    servicio: ServicioAdministracionUsuarios = Depends(obtener_servicio_administracion_usuarios),
) -> list[RespuestaUsuario]:
    try:
        usuarios = servicio.listar_usuarios(id_usuario_solicitante)
    except PermisoDenegadoError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except IdentificadorInvalidoError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return [RespuestaUsuario(**u.__dict__) for u in usuarios]


@app.get("/usuarios/{id_usuario}", response_model=RespuestaUsuario)
def obtener_usuario(
    id_usuario: str,
    id_usuario_solicitante: str,
    servicio: ServicioAdministracionUsuarios = Depends(obtener_servicio_administracion_usuarios),
) -> RespuestaUsuario:
    try:
        usuario = servicio.obtener_usuario(id_usuario_solicitante, id_usuario)
    except PermisoDenegadoError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except UsuarioNoEncontradoError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except IdentificadorInvalidoError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return RespuestaUsuario(**usuario.__dict__)


@app.delete("/usuarios/{id_usuario}", status_code=204)
def eliminar_usuario(
    id_usuario: str,
    id_usuario_solicitante: str,
    servicio: ServicioAdministracionUsuarios = Depends(obtener_servicio_administracion_usuarios),
) -> None:
    try:
        servicio.eliminar_usuario(id_usuario_solicitante, id_usuario)
    except PermisoDenegadoError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except UsuarioNoEncontradoError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except UsuarioConSimulacionesError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except IdentificadorInvalidoError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.patch("/usuarios/{id_usuario}/rol", response_model=RespuestaUsuario)
def cambiar_rol_usuario(
    id_usuario: str,
    id_usuario_solicitante: str,
    solicitud: SolicitudCambioRol,
    servicio: ServicioAdministracionUsuarios = Depends(obtener_servicio_administracion_usuarios),
) -> RespuestaUsuario:
    try:
        usuario = servicio.cambiar_rol(id_usuario_solicitante, id_usuario, solicitud.nuevo_rol)
    except PermisoDenegadoError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except UsuarioNoEncontradoError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except IdentificadorInvalidoError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return RespuestaUsuario(**usuario.__dict__)


@app.get("/alertas/{id_usuario}", response_model=list[RespuestaAlerta])
def listar_alertas(
    id_usuario: str,
    repositorio: RepositorioAlertas = Depends(obtener_repositorio_alertas),
    autorizacion: ServicioAutorizacionRoles = Depends(obtener_servicio_autorizacion_roles),
) -> list[RespuestaAlerta]:
    _exigir_inversionista(id_usuario, autorizacion)
    try:
        alertas = repositorio.listar_por_usuario(id_usuario)
    except IdentificadorInvalidoError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return [RespuestaAlerta(**a.__dict__) for a in alertas]


# --- Dashboard (solo ADMINISTRADOR) ---------------------------------------

@app.get("/dashboard/estadisticas", response_model=RespuestaEstadisticas)
def obtener_estadisticas(
    id_usuario_solicitante: str,
    servicio: ServicioDashboard = Depends(obtener_servicio_dashboard),
) -> RespuestaEstadisticas:
    try:
        estadisticas = servicio.obtener_estadisticas(id_usuario_solicitante)
    except PermisoDenegadoError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except IdentificadorInvalidoError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return RespuestaEstadisticas(**estadisticas.__dict__)


@app.get("/dashboard/operacion", response_model=RespuestaOperacionTI)
def obtener_estado_operacion(
    id_usuario_solicitante: str,
    servicio: ServicioOperacionTI = Depends(obtener_servicio_operacion_ti),
) -> RespuestaOperacionTI:
    try:
        estado = servicio.obtener_estado(id_usuario_solicitante)
    except PermisoDenegadoError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except IdentificadorInvalidoError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return RespuestaOperacionTI(**estado.__dict__)


# El panel visual se sirve desde el mismo backend para que exista un único
# enlace local (http://127.0.0.1:8000) y no haya que abrir archivos a mano.
# Se monta al final para no interceptar las rutas de la API ni /docs.
_FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
if _FRONTEND.is_dir():
    app.mount("/", StaticFiles(directory=_FRONTEND, html=True), name="frontend")
