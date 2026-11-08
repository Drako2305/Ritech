/**
 * Como el backend no emite token de sesión (ver dominio del proyecto),
 * el "login" del frontend consiste en guardar los datos del usuario
 * autenticado en sessionStorage (se pierde al cerrar la pestaña) y
 * volver a mandarlos como id_usuario_solicitante en cada llamada que
 * lo requiera. Esto es una conveniencia de UI, no un mecanismo de
 * seguridad: cualquiera con acceso a la consola del navegador podría
 * modificarlo (misma limitación ya documentada en el backend).
 */
class SesionUsuario {
  static CLAVE = "ritech_usuario";

  static guardar(usuario) {
    sessionStorage.setItem(SesionUsuario.CLAVE, JSON.stringify(usuario));
  }

  static obtener() {
    const datos = sessionStorage.getItem(SesionUsuario.CLAVE);
    return datos ? JSON.parse(datos) : null;
  }

  static cerrar() {
    sessionStorage.removeItem(SesionUsuario.CLAVE);
  }

  static esAdministrador(usuario) {
    return Boolean(usuario) && usuario.rol === "ADMINISTRADOR";
  }

  static paginaInicial(usuario) {
    if (usuario.rol === "ADMINISTRADOR") return "admin.html";
    if (usuario.rol === "GESTOR_TI") return "operacion.html";
    return "simular.html";
  }

  /** Redirige a index.html si no hay sesión activa; retorna el usuario si sí la hay. */
  static exigirSesion() {
    const usuario = SesionUsuario.obtener();
    if (!usuario) {
      window.location.href = "index.html";
      return null;
    }
    return usuario;
  }

  static exigirRol(rolesPermitidos) {
    const usuario = SesionUsuario.exigirSesion();
    if (usuario && !rolesPermitidos.includes(usuario.rol)) {
      window.location.href = SesionUsuario.paginaInicial(usuario);
      return null;
    }
    return usuario;
  }
}
