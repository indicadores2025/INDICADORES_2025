import sqlite3
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

responder_bp = Blueprint('responder', __name__, template_folder="../templates")

def get_db():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------------
# PANEL DE RESPUESTAS DEL USUARIO
# -------------------------------
@responder_bp.route("/responder", methods=["GET", "POST"])
def responder():
    if "usuario" not in session or session["tipo"] != "usuario":
        return redirect("/login")

    db = get_db()
    usuario_nombre = session["usuario"]
    usuario = db.execute("SELECT * FROM usuarios WHERE nombre=?", (usuario_nombre,)).fetchone()

    # Verificar si hay periodo abierto
    periodo = db.execute("SELECT * FROM periodo WHERE abierto=1").fetchone()
    if not periodo:
        return render_template("responder.html", periodo_abierto=False)

    mes, año = periodo["mes"], periodo["año"]

    # Procesar respuesta
    if request.method == "POST":
        pregunta_id = request.form["pregunta_id"]
        valor = request.form["valor"]
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Verificar si ya existe una respuesta
        existente = db.execute("""
            SELECT * FROM respuestas
            WHERE pregunta_id=? AND usuario_id=? AND mes=? AND año=?
        """, (pregunta_id, usuario["id"], mes, año)).fetchone()

        if existente:
            flash("⚠️ Ya has respondido esta pregunta. No puedes modificarla nuevamente.", "warning")
        else:
            db.execute("""
                INSERT INTO respuestas (pregunta_id, usuario_id, valor, mes, año, fecha_ingreso)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pregunta_id, usuario["id"], valor, mes, año, fecha))
            db.commit()
            flash("✅ Respuesta registrada correctamente", "success")

        return redirect(url_for("responder.responder"))

    # Obtener preguntas asignadas al usuario
    preguntas = db.execute("""
        SELECT p.id, p.texto, p.tipo, p.afecta_presupuesto,
               pr.nombre AS presupuesto, u.nombre AS unidad,
               r.valor AS respuesta
        FROM preguntas p
        LEFT JOIN presupuesto pr ON p.presupuesto_id = pr.id
        LEFT JOIN unidad u ON p.unidad_id = u.id
        LEFT JOIN respuestas r
            ON r.pregunta_id = p.id AND r.usuario_id = ? AND r.mes = ? AND r.año = ?
        WHERE p.usuario_id = ? AND p.activo = 1
        ORDER BY p.id ASC
    """, (usuario["id"], mes, año, usuario["id"])).fetchall()

    return render_template("responder.html", preguntas=preguntas, periodo=periodo, periodo_abierto=True)
