import sqlite3
from flask import Blueprint, render_template, request
from datetime import datetime

graficos_bp = Blueprint("graficos", __name__, template_folder="../templates")

def get_db():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@graficos_bp.route("/graficos", methods=["GET", "POST"])
def graficos():
    db = get_db()

    # Datos para filtros
    preguntas = db.execute("SELECT id, texto FROM preguntas WHERE activo=1").fetchall()
    unidades = db.execute("SELECT id, nombre FROM unidad WHERE activo=1").fetchall()
    usuarios = db.execute("SELECT id, nombre FROM usuarios WHERE activo=1").fetchall()

    # Variables de salida
    datos1, datos2 = {}, {}
    anio_actual = datetime.now().year

    # Determinar cuál formulario se envió (grafico1 o grafico2)
    accion = request.form.get("accion")

    # ====================================================
    # 📊 GRÁFICO 1 — ESTADÍSTICAS ANUALES
    # ====================================================
    if accion == "grafico1":
        tipo_grafico = request.form.get("tipo_grafico")
        pregunta_id = request.form.get("pregunta")
        unidad_id = request.form.get("unidad")
        usuario_id = request.form.get("usuario")
        anio = request.form.get("anio") or str(anio_actual)

        query = """
            SELECT r.mes, AVG(CAST(r.valor AS FLOAT)) as promedio
            FROM respuestas r
            JOIN preguntas p ON p.id = r.pregunta_id
            WHERE p.id = ? AND r.año = ?
        """
        params = [pregunta_id, anio]

        if unidad_id and unidad_id != "0":
            query += " AND p.unidad_id = ?"
            params.append(unidad_id)
        if usuario_id and usuario_id != "0":
            query += " AND r.usuario_id = ?"
            params.append(usuario_id)

        query += " GROUP BY r.mes ORDER BY r.mes"

        resultados = db.execute(query, tuple(params)).fetchall()

        meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                 "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
        valores = []
        for m in meses:
            v = next((r["promedio"] for r in resultados if r["mes"].lower() == m.lower()), 0)
            valores.append(v or 0)

        datos1 = {
            "tipo_grafico": tipo_grafico,
            "labels": meses,
            "valores": valores,
            "anio": anio,
        }

    # ====================================================
    # 📊 GRÁFICO 2 — COMPARATIVO ENTRE DOS PERÍODOS
    # ====================================================
    elif accion == "grafico2":
        tipo_grafico = request.form.get("tipo_grafico2")
        pregunta_id = request.form.get("pregunta2")
        unidad_id = request.form.get("unidad2")
        usuario_id = request.form.get("usuario2")
        mes1 = request.form.get("mes1")
        anio1 = request.form.get("anio1")
        mes2 = request.form.get("mes2")
        anio2 = request.form.get("anio2")

        def obtener_valor(mes, anio):
            q = """
                SELECT AVG(CAST(r.valor AS FLOAT)) as promedio
                FROM respuestas r
                JOIN preguntas p ON p.id = r.pregunta_id
                WHERE p.id = ? AND r.mes = ? AND r.año = ?
            """
            params = [pregunta_id, mes, anio]
            if unidad_id and unidad_id != "0":
                q += " AND p.unidad_id = ?"
                params.append(unidad_id)
            if usuario_id and usuario_id != "0":
                q += " AND r.usuario_id = ?"
                params.append(usuario_id)
            return db.execute(q, tuple(params)).fetchone()["promedio"] or 0

        v1 = obtener_valor(mes1, anio1)
        v2 = obtener_valor(mes2, anio2)
        diff = round(v2 - v1, 2)

        datos2 = {
            "tipo_grafico": tipo_grafico,
            "labels": [f"{mes1} {anio1}", f"{mes2} {anio2}"],
            "valores": [v1, v2],
            "mes1": mes1, "anio1": anio1,
            "mes2": mes2, "anio2": anio2,
            "diferencia": diff,
        }

    return render_template(
        "graficos.html",
        preguntas=preguntas,
        unidades=unidades,
        usuarios=usuarios,
        datos1=datos1,
        datos2=datos2,
        anio_actual=anio_actual
    )
