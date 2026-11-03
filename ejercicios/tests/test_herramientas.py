import pytest

from conftest import HOST_EJEMPLO, resolvedor_publico
from gemela import extractor, herramientas
from gemela.lector import leer_sitio


def _crear_app(conn, nombre="X"):
    uid = conn.execute(
        "INSERT INTO usuarios (proveedor, id_proveedor, nombre) VALUES ('github', %s, 'Ana') ON CONFLICT DO NOTHING RETURNING id",
        (nombre,)).fetchone()["id"]
    return conn.execute(
        "INSERT INTO apps (usuario_id, url, nombre, descripcion, token_verificacion) VALUES (%s,'https://x.example',%s,'d','t') RETURNING id",
        (uid, nombre)).fetchone()["id"]


@pytest.fixture
def app_id(conn, transporte_ejemplo):
    paginas = leer_sitio(f"https://{HOST_EJEMPLO}/", resolvedor=resolvedor_publico, transporte=transporte_ejemplo)
    app = _crear_app(conn)
    extractor.guardar_contenido(conn, app, extractor.analizar(paginas))
    return app


def test_buscar_encuentra_el_fragmento_con_su_url(conn, app_id):
    r = herramientas.buscar(conn, app_id, "horario viernes")
    assert r[0]["url"].endswith("/horarios.html") and "viernes" in r[0]["fragmento"]


def test_buscar_con_una_pregunta_en_lenguaje_natural(conn, app_id):
    r = herramientas.buscar(conn, app_id, "¿A qué hora abren los viernes?")
    assert r and r[0]["url"].endswith("/horarios.html")


def test_c23_buscar_sin_coincidencias_devuelve_lista_vacia(conn, app_id):
    assert herramientas.buscar(conn, app_id, "astronomía cuántica") == []
    assert herramientas.buscar(conn, app_id, "") == []
    assert herramientas.buscar(conn, app_id, "a de la") == []  # solo palabras vacías


def test_buscar_limites_de_5_fragmentos_de_500_caracteres(conn):
    app = _crear_app(conn, "Grande")
    for i in range(12):
        conn.execute("INSERT INTO contenido (app_id, url, titulo, texto) VALUES (%s, %s, %s, %s)",
                     (app, f"https://x.example/{i}", f"Pan {i}", "pan fresco " * 300))
    r = herramientas.buscar(conn, app, "pan")
    assert len(r) == 5 and all(len(f["fragmento"]) <= 500 for f in r)


def test_buscar_no_mezcla_apps(conn, app_id):
    otra = _crear_app(conn, "Otra")
    conn.execute("INSERT INTO contenido (app_id, url, titulo, texto) VALUES (%s,'https://o.example/','Otra','jardinería y plantas')", (otra,))
    assert herramientas.buscar(conn, otra, "horarios") == []
    assert herramientas.buscar(conn, app_id, "jardinería") == []


@pytest.mark.parametrize("consulta", ["'; DROP TABLE apps; --", "a | b & !c", "(((", "\x00pan"])
def test_buscar_resiste_consultas_con_sintaxis_de_busqueda(conn, app_id, consulta):
    herramientas.buscar(conn, app_id, consulta.replace("\x00", ""))
    assert conn.execute("SELECT count(*) AS n FROM apps").fetchone()["n"] == 1


def test_contacto_y_listar_paginas(conn, app_id):
    assert herramientas.contacto(conn, app_id)["correos"] == ["hola@laespiga.example"]
    titulos = [p["titulo"] for p in herramientas.listar_paginas(conn, app_id)]
    assert sorted(titulos) == ["Contacto", "Horarios", "Panadería La Espiga"]


def test_contacto_sin_datos_devuelve_listas_vacias(conn):
    app = _crear_app(conn, "Sin")
    assert herramientas.contacto(conn, app) == {"correos": [], "telefonos": [], "direcciones": []}


def test_ninguna_herramienta_escribe_en_la_base(conn, app_id):
    conn.commit()
    conn.execute("SET TRANSACTION READ ONLY")
    for nombre, args in [("buscar", {"consulta": "pan"}), ("contacto", {}), ("listar_paginas", {})]:
        herramientas.ejecutar(conn, app_id, nombre, args)  # una escritura lanzaría ReadOnlySqlTransaction


def test_ejecutar_valida_nombre_y_argumentos(conn, app_id):
    with pytest.raises(herramientas.ErrorHerramienta):
        herramientas.ejecutar(conn, app_id, "borrar_todo", {})
    with pytest.raises(herramientas.ErrorHerramienta):
        herramientas.ejecutar(conn, app_id, "buscar", {"consulta": 5})
    with pytest.raises(herramientas.ErrorHerramienta):
        herramientas.ejecutar(conn, app_id, "buscar", {})


def test_definiciones_cubren_las_tres_herramientas():
    assert set(herramientas.DEFINICIONES) == {"buscar", "contacto", "listar_paginas"}
