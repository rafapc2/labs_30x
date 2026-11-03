import pytest

from conftest import HOST_EJEMPLO, resolvedor_publico
from gemela import extractor
from gemela.lector import Pagina, leer_sitio


@pytest.fixture
def paginas(transporte_ejemplo):
    return leer_sitio(f"https://{HOST_EJEMPLO}/", resolvedor=resolvedor_publico, transporte=transporte_ejemplo)


def _usuario_y_app(conn):
    uid = conn.execute("INSERT INTO usuarios (proveedor, id_proveedor, nombre) VALUES ('github','1','Ana') RETURNING id").fetchone()["id"]
    return conn.execute(
        "INSERT INTO apps (usuario_id, url, nombre, descripcion, token_verificacion) VALUES (%s,'https://x.example','X','d','t') RETURNING id",
        (uid,)).fetchone()["id"]


def test_contenido_queda_con_una_fila_por_pagina(conn, paginas):
    app = _usuario_y_app(conn)
    extractor.guardar_contenido(conn, app, extractor.analizar(paginas))
    filas = conn.execute("SELECT titulo FROM contenido WHERE app_id = %s ORDER BY titulo", (app,)).fetchall()
    assert [f["titulo"] for f in filas] == ["Contacto", "Horarios", "Panadería La Espiga"]


def test_contacto_del_sitio_de_ejemplo(paginas):
    c = extractor.extraer_contacto(paginas)
    assert c["correos"] == ["hola@laespiga.example"]
    assert c["telefonos"] == ["+34 600 123 456"]
    assert c["direcciones"] == ["Calle Mayor 12, 28013 Madrid"]


def test_contacto_se_guarda_en_la_app(conn, paginas):
    app = _usuario_y_app(conn)
    extractor.guardar_contenido(conn, app, extractor.analizar(paginas))
    assert conn.execute("SELECT contacto FROM apps WHERE id = %s", (app,)).fetchone()["contacto"]["correos"] == ["hola@laespiga.example"]


def test_sin_contacto_queda_vacio_y_no_se_inventa():
    c = extractor.extraer_contacto([Pagina("https://x.example/", "<html><body>Solo texto sin datos. Año 2024, código 12345.</body></html>")])
    assert c == {"correos": [], "telefonos": [], "direcciones": []}


def test_enlaces_mailto_y_tel_y_etiqueta_address():
    html = '<a href="mailto:a@b.example?subject=x">c</a><a href="tel:+52 55 1234 5678">t</a><address>Av. Sol 5, Lima</address>'
    c = extractor.extraer_contacto([Pagina("https://x.example/", html)])
    assert c["correos"] == ["a@b.example"] and c["telefonos"] == ["+52 55 1234 5678"] and c["direcciones"] == ["Av. Sol 5, Lima"]


def test_extrae_titulo_y_quita_scripts_y_estilos():
    p = extractor.extraer_pagina(Pagina("https://x.example/", "<title> Hola </title><style>a{}</style><script>var x=1</script><p>Texto   útil</p>"))
    assert p.titulo == "Hola" and p.texto == "Hola Texto útil"
    assert "var x" not in p.texto and "a{}" not in p.texto


@pytest.mark.parametrize("tope", [0, 1, 50, 200, 100000])
def test_el_texto_para_el_modelo_nunca_supera_el_tope(tope):
    grande = [extractor.PaginaExtraida(f"https://x.example/{i}", f"T{i}", "palabra " * 500) for i in range(10)]
    texto = extractor.texto_para_modelo(extractor.Analisis(grande), tope=tope)
    assert len(texto) <= tope


def test_el_tope_por_defecto_es_30000(monkeypatch):
    grande = [extractor.PaginaExtraida(f"https://x.example/{i}", "T", "palabra " * 2000) for i in range(10)]
    assert len(extractor.texto_para_modelo(extractor.Analisis(grande))) == 30000
