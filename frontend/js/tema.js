/** Modo claro/oscuro (SCRUM-4), guardado en localStorage (persiste entre páginas). */
class GestorTema {
  static CLAVE = "ritech_tema";

  static aplicarGuardado() {
    const tema = localStorage.getItem(GestorTema.CLAVE) || "claro";
    document.documentElement.setAttribute("data-tema", tema);
    GestorTema.actualizarControl();
  }

  static alternar() {
    const actual = document.documentElement.getAttribute("data-tema");
    const nuevo = actual === "oscuro" ? "claro" : "oscuro";
    document.documentElement.setAttribute("data-tema", nuevo);
    localStorage.setItem(GestorTema.CLAVE, nuevo);
    GestorTema.actualizarControl();
  }

  static actualizarControl() {
    const boton = document.getElementById("boton-tema");
    if (!boton) return;
    const modoOscuro = document.documentElement.getAttribute("data-tema") === "oscuro";
    boton.textContent = modoOscuro ? "☀" : "☾";
    boton.title = modoOscuro ? "Cambiar a modo claro" : "Cambiar a modo oscuro";
    boton.setAttribute("aria-label", boton.title);
  }
}

GestorTema.aplicarGuardado();
