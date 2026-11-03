import psycopg
import pytest

from gemela import db


def _usuario(conn):
    return conn.execute(
        "INSERT INTO usuarios (proveedor, id_proveedor, nombre) VALUES ('github', '1', 'Ana') RETURNING id"
    ).fetchone()["id"]


def _app(conn, usuario_id):
    return conn.execute(
        "INSERT INTO apps (usuario_id, url, nombre, descripcion, token_verificacion) "
        "VALUES (%s, 'https://ejemplo.com', 'Ejemplo', 'Desc', 'tok') RETURNING id",
        (usuario_id,),
    ).fetchone()["id"]


def test_migraciones_se_aplican_y_se_revierten(url_bd):
    with db.conectar(url_bd) as c:
        db.revertir(c, pasos=10)
        tablas = {r["tablename"] for r in c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
        assert "apps" not in tablas
        assert db.aplicar(c) == ["0001_inicial", "0002_descripcion_corta"]
        tablas = {r["tablename"] for r in c.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
        assert {"usuarios", "apps", "contenido", "herramientas", "llamadas"} <= tablas
        assert db.aplicar(c) == []  # idempotente


def test_llamadas_no_guarda_el_texto_de_la_consulta(conn):
    cols = {r["column_name"] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'llamadas'")}
    assert cols == {"id", "app_id", "herramienta", "fecha", "resultado"}


def test_indice_de_texto_completo_encuentra_contenido(conn):
    app = _app(conn, _usuario(conn))
    conn.execute(
        "INSERT INTO contenido (app_id, url, titulo, texto) VALUES (%s, 'https://ejemplo.com/a', 'Horarios', "
        "'Abrimos de lunes a viernes por la mañana')", (app,))
    filas = conn.execute(
        "SELECT titulo FROM contenido WHERE tsv @@ plainto_tsquery('spanish', %s)", ("horario viernes",)
    ).fetchall()
    assert [f["titulo"] for f in filas] == ["Horarios"]
    indices = {r["indexname"] for r in conn.execute("SELECT indexname FROM pg_indexes WHERE tablename='contenido'")}
    assert "contenido_tsv" in indices


def test_estado_invalido_se_rechaza(conn):
    uid = _usuario(conn)
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "INSERT INTO apps (usuario_id, url, nombre, descripcion, token_verificacion, estado) "
            "VALUES (%s, 'u', 'n', 'd', 't', 'rara')", (uid,))
