/**
 * Cliente HTTP hacia el backend RiTech. Centraliza fetch() y el manejo de
 * errores para que las páginas no repitan lógica de red.
 */
class ApiCliente {
  constructor(urlBase) {
    this._urlBase = urlBase;
  }

  async _peticion(metodo, ruta, { cuerpo, params } = {}) {
    let url = this._urlBase + ruta;
    if (params) {
      url += "?" + new URLSearchParams(params).toString();
    }

    const opciones = { method: metodo, headers: {} };
    if (cuerpo !== undefined) {
      opciones.headers["Content-Type"] = "application/json";
      opciones.body = JSON.stringify(cuerpo);
    }

    let respuesta;
    try {
      respuesta = await fetch(url, opciones);
    } catch (error) {
      throw new Error("No se pudo conectar con el backend. Verifica que el servidor esté corriendo.");
    }

    let datos = null;
    try {
      datos = await respuesta.json();
    } catch (_) {
      // Respuestas sin cuerpo (204 No Content), no es un error.
    }

    if (!respuesta.ok) {
      const mensaje = (datos && datos.detail) ? datos.detail : `Error ${respuesta.status}`;
      throw new Error(mensaje);
    }
    return datos;
  }

  registrarUsuario(datos) {
    return this._peticion("POST", "/usuarios", { cuerpo: datos });
  }

  iniciarSesion(datos) {
    return this._peticion("POST", "/login", { cuerpo: datos });
  }

  crearSimulacion(datos) {
    return this._peticion("POST", "/simulaciones", { cuerpo: datos });
  }

  listarSimulaciones(idUsuario) {
    return this._peticion("GET", `/simulaciones/${idUsuario}`);
  }

  listarAlertas(idUsuario) {
    return this._peticion("GET", `/alertas/${idUsuario}`);
  }

  obtenerCotizacion() {
    return this._peticion("GET", "/mercado/cotizacion");
  }

  listarUsuarios(idUsuarioSolicitante) {
    return this._peticion("GET", "/usuarios", {
      params: { id_usuario_solicitante: idUsuarioSolicitante },
    });
  }

  eliminarUsuario(idUsuarioObjetivo, idUsuarioSolicitante) {
    return this._peticion("DELETE", `/usuarios/${idUsuarioObjetivo}`, {
      params: { id_usuario_solicitante: idUsuarioSolicitante },
    });
  }

  cambiarRol(idUsuarioObjetivo, idUsuarioSolicitante, nuevoRol) {
    return this._peticion("PATCH", `/usuarios/${idUsuarioObjetivo}/rol`, {
      params: { id_usuario_solicitante: idUsuarioSolicitante },
      cuerpo: { nuevo_rol: nuevoRol },
    });
  }

  obtenerEstadisticas(idUsuarioSolicitante) {
    return this._peticion("GET", "/dashboard/estadisticas", {
      params: { id_usuario_solicitante: idUsuarioSolicitante },
    });
  }

  obtenerEstadoOperacion(idUsuarioSolicitante) {
    return this._peticion("GET", "/dashboard/operacion", {
      params: { id_usuario_solicitante: idUsuarioSolicitante },
    });
  }
}

// Si el panel se sirve desde el propio backend, la API vive en el mismo
// origen. Si se abre el HTML como archivo, se usa el puerto local de uvicorn.
function resolverBaseApi() {
  if (window.location.protocol === "file:") return "http://127.0.0.1:8000";
  if (window.location.port === "8000" || window.location.port === "") {
    return window.location.origin;
  }
  return "http://127.0.0.1:8000";
}

const API_BASE_URL = resolverBaseApi();
const api = new ApiCliente(API_BASE_URL);
