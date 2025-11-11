import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash

unidad_bp = Blueprint('unidad', __name__, template_folder="../templates")

def get_db():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@unidad_bp.route("/unidad", methods=["GET", "POST"])
def unidad():
    db = get_db()

    if request.method == "POST":
        nombre = request.form["nombre"]
        db.execute("INSERT INTO unidad (nombre, activo) VALUES (?, 1)", (nombre,))
        db.commit()
        flash("✅ Unidad agregada correctamente", "success")
        return redirect(url_for("unidad.unidad"))

    search = request.args.get("search", "")
    if search:
        unidades = db.execute("SELECT * FROM unidad WHERE nombre LIKE ?", ('%' + search + '%',)).fetchall()
    else:
        unidades = db.execute("SELECT * FROM unidad").fetchall()

    return render_template("unidad.html", unidades=unidades, search=search)

@unidad_bp.route("/unidad/desactivar/<int:id>")
def desactivar_unidad(id):
    db = get_db()
    unidad = db.execute("SELECT activo FROM unidad WHERE id=?", (id,)).fetchone()
    nuevo_estado = 0 if unidad["activo"] == 1 else 1
    db.execute("UPDATE unidad SET activo=? WHERE id=?", (nuevo_estado, id))
    db.commit()
    flash("⚙️ Estado de la unidad actualizado", "info")
    return redirect(url_for("unidad.unidad"))
