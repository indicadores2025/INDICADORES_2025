import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash

usuario_bp = Blueprint('usuario', __name__, template_folder="../templates")

def get_db():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@usuario_bp.route("/usuarios", methods=["GET", "POST"])
def usuarios():
    db = get_db()
    unidades = db.execute("SELECT * FROM unidad WHERE activo=1").fetchall()

    if request.method == "POST":
        nombre = request.form["nombre"]
        contrasena = request.form["contrasena"]
        tipo = request.form["tipo"]
        unidad_id = request.form["unidad_id"]
        db.execute("INSERT INTO usuarios (nombre, contrasena, tipo, unidad_id, activo) VALUES (?, ?, ?, ?, 1)",
                   (nombre, contrasena, tipo, unidad_id))
        db.commit()
        flash("✅ Usuario creado correctamente", "success")
        return redirect(url_for("usuario.usuarios"))

    search = request.args.get("search", "")
    if search:
        users = db.execute("""
        SELECT u.id, u.nombre, u.tipo, u.activo, un.nombre AS unidad_nombre
        FROM usuarios u
        LEFT JOIN unidad un ON u.unidad_id = un.id
        WHERE u.nombre LIKE ?""", ('%' + search + '%',)).fetchall()
    else:
        users = db.execute("""
        SELECT u.id, u.nombre, u.tipo, u.activo, un.nombre AS unidad_nombre
        FROM usuarios u
        LEFT JOIN unidad un ON u.unidad_id = un.id""").fetchall()

    return render_template("usuarios.html", users=users, unidades=unidades, search=search)

@usuario_bp.route("/usuarios/desactivar/<int:id>")
def desactivar_usuario(id):
    db = get_db()
    usuario = db.execute("SELECT activo FROM usuarios WHERE id=?", (id,)).fetchone()
    nuevo_estado = 0 if usuario["activo"] == 1 else 1
    db.execute("UPDATE usuarios SET activo=? WHERE id=?", (nuevo_estado, id))
    db.commit()
    flash("⚙️ Estado del usuario actualizado", "info")
    return redirect(url_for("usuario.usuarios"))
