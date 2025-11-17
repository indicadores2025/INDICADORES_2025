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

    # Verificar periodo abierto
    periodo = db.execute("SELECT * FROM periodo WHERE abierto=1").fetchone()
    if not periodo:
        return render_template("responder.html", periodo_abierto=False)

    mes, año = periodo["mes"], periodo["año"]

    # 🔹 GUARDAR TODAS LAS RESPUESTAS EN UN SOLO ENVÍO
    if request.method == "POST":
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_guardadas = 0
        total_omitidas = 0

        for key, valor in request.form.items():
            if key.startswith("pregunta_") and valor.strip() != "":
                pregunta_id = key.split("_")[1]

                # Verificar si ya existe una respuesta
                existente = db.execute("""
                    SELECT id FROM respuestas
                    WHERE pregunta_id=? AND usuario_id=? AND mes=? AND año=?
                """, (pregunta_id, usuario["id"], mes, año)).fetchone()

                if existente:
                    total_omitidas += 1
                    continue

                db.execute("""
                    INSERT INTO respuestas (pregunta_id, usuario_id, valor, mes, año, fecha_ingreso)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (pregunta_id, usuario["id"], valor.strip(), mes, año, fecha))
                total_guardadas += 1

        db.commit()
        flash(f"✅ Se registraron {total_guardadas} respuestas nuevas. {total_omitidas} ya estaban respondidas.", "success")
        return redirect(url_for("responder.responder"))

    # 🔹 Mostrar preguntas asignadas
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
