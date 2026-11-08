"""Excepciones del dominio de simulación de inversiones RiTech."""

from decimal import Decimal


class CapitalInsuficienteError(Exception):
    """Se lanza cuando el capital inicial no cumple el mínimo permitido."""

    def __init__(self, capital_ingresado: Decimal, capital_minimo: Decimal):
        self.capital_ingresado = capital_ingresado
        self.capital_minimo = capital_minimo
        super().__init__(
            f"El capital ingresado (${capital_ingresado:,.0f} COP) es menor "
            f"al mínimo permitido (${capital_minimo:,.0f} COP)."
        )


class ErrorGeneracionVariacion(Exception):
    """Se lanza cuando no se puede obtener/generar la variación del NASDAQ."""


class UsuarioNoEncontradoError(Exception):
    """Se lanza cuando se intenta simular con un id_usuario que no existe."""

    def __init__(self, id_usuario: str):
        self.id_usuario = id_usuario
        super().__init__(f"El usuario '{id_usuario}' no existe.")


class CorreoDuplicadoError(Exception):
    """Se lanza al registrar un usuario con un correo ya existente."""

    def __init__(self, correo: str):
        self.correo = correo
        super().__init__(f"Ya existe un usuario registrado con el correo '{correo}'.")


class CredencialesInvalidasError(Exception):
    """Se lanza en /login cuando el correo no existe o la contraseña no coincide.

    El mensaje es deliberadamente genérico (no dice cuál de los dos falló)
    para no darle pistas a quien intenta adivinar credenciales.
    """

    def __init__(self):
        super().__init__("Correo o contraseña incorrectos.")


class ErrorGeneracionAlerta(Exception):
    """Se lanza cuando falla la generación de una alerta con IA.

    Es un error "no crítico" a propósito: la simulación ya se guardó antes
    de intentar generar la alerta, así que quien la atrapa (ServicioAlertas)
    simplemente se queda sin alerta en vez de deshacer la simulación.
    """


class ErrorConsultaNoticias(Exception):
    """Se lanza cuando falla la consulta de noticias financieras externas.

    GeneradorAlertaGemini la atrapa y la relanza como ErrorGeneracionAlerta,
    para que ServicioAlertas la trate igual que cualquier otro fallo de IA."""


class PermisoDenegadoError(Exception):
    """Se lanza cuando quien hace la petición no tiene rol ADMINISTRADOR."""

    def __init__(self):
        super().__init__("No tiene permisos para realizar esta acción.")


class UsuarioConSimulacionesError(Exception):
    """Se lanza al intentar eliminar un usuario que ya tiene simulaciones
    registradas (la llave foránea en `simulaciones` lo impide)."""

    def __init__(self, id_usuario: str):
        self.id_usuario = id_usuario
        super().__init__(
            f"No se puede eliminar el usuario '{id_usuario}' porque tiene "
            "simulaciones registradas."
        )


class IdentificadorInvalidoError(Exception):
    """Se lanza cuando un id recibido no tiene formato UUID válido (p. ej.
    quien llama a la API dejó el valor de ejemplo "string" de Swagger)."""

    def __init__(self, identificador: str):
        self.identificador = identificador
        super().__init__(f"El identificador '{identificador}' no tiene un formato válido.")
