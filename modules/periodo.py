import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash

periodo_bp = Blueprint('periodo', __name__, template_folder="../templates")

def get_db():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@periodo_bp.route("/periodo", methods=["GET", "POST"])
def periodo():
    db = get_db()

    # Crear o abrir un nuevo periodo
    if request.method == "POST":
        mes = request.form["mes"]
        año = request.form["año"]
        db.execute("UPDATE periodo SET abierto=0")
        db.execute("INSERT INTO periodo (mes, año, abierto) VALUES (?, ?, 1)", (mes, año))
        db.commit()
        flash(f"📅 Periodo {mes}/{año} abierto correctamente", "success")
        return redirect(url_for("periodo.periodo"))

    periodos = db.execute("SELECT * FROM periodo ORDER BY id DESC").fetchall()
    abierto = db.execute("SELECT * FROM periodo WHERE abierto=1").fetchone()
    return render_template("periodo.html", periodos=periodos, abierto=abierto)

@periodo_bp.route("/periodo/cerrar/<int:id>")
def cerrar_periodo(id):
    db = get_db()
    db.execute("UPDATE periodo SET abierto=0 WHERE id=?", (id,))
    db.commit()
    flash("🔒 Periodo cerrado correctamente", "info")
    return redirect(url_for("periodo.periodo"))

@periodo_bp.route("/periodo/abrir/<int:id>")
def abrir_periodo(id):
    db = get_db()
    db.execute("UPDATE periodo SET abierto=0")
    db.execute("UPDATE periodo SET abierto=1 WHERE id=?", (id,))
    db.commit()
    flash("✅ Periodo abierto correctamente", "success")
    return redirect(url_for("periodo.periodo"))

@periodo_bp.route("/periodo/editar/<int:id>", methods=["GET", "POST"])
def editar_periodo(id):
    db = get_db()
    if request.method == "POST":
        mes = request.form["mes"]
        año = request.form["año"]
        db.execute("UPDATE periodo SET mes=?, año=? WHERE id=?", (mes, año, id))
        db.commit()
        flash("✏️ Periodo actualizado correctamente", "success")
        return redirect(url_for("periodo.periodo"))

    periodo = db.execute("SELECT * FROM periodo WHERE id=?", (id,)).fetchone()
    return render_template("editar_periodo.html", periodo=periodo)
