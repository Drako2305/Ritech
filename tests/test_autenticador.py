from servicios.autenticador import Autenticador


def test_verifica_la_contrasena_correcta():
    autenticador = Autenticador()
    hash_guardado = autenticador.hashear("mi-clave-secreta")
    assert autenticador.verificar("mi-clave-secreta", hash_guardado) is True


def test_rechaza_la_contrasena_incorrecta():
    autenticador = Autenticador()
    hash_guardado = autenticador.hashear("mi-clave-secreta")
    assert autenticador.verificar("otra-clave", hash_guardado) is False


def test_el_hash_nunca_es_igual_a_la_contrasena_en_texto_plano():
    autenticador = Autenticador()
    assert autenticador.hashear("mi-clave-secreta") != "mi-clave-secreta"
