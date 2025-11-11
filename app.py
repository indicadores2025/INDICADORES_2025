from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO
import sqlite3

# Importar módulos
from modules.unidad import unidad_bp
from modules.usuario import usuario_bp
from modules.presupuesto import presupuesto_bp
from modules.periodo import periodo_bp
from modules.preguntas import preguntas_bp
from modules.graficos import graficos_bp
from modules.responder import responder_bp
from modules.auditoria import auditoria_bp
from modules.presupuesto import calcular_resumen_presupuesto


app = Flask(__name__)
app.secret_key = "clave_secreta_2025"
socketio = SocketIO(app)

# Registrar los módulos
app.register_blueprint(unidad_bp)
app.register_blueprint(usuario_bp)
app.register_blueprint(presupuesto_bp)
app.register_blueprint(periodo_bp)
app.register_blueprint(preguntas_bp)
app.register_blueprint(graficos_bp)
app.register_blueprint(responder_bp)
app.register_blueprint(auditoria_bp)


def get_db():
    conn = sqlite3.connect("database/data.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    db = get_db()
    if request.method == "POST":
        usuario = request.form["usuario"]
        contrasena = request.form["contrasena"]
        user = db.execute("SELECT * FROM usuarios WHERE nombre=? AND contrasena=?", (usuario, contrasena)).fetchone()
        if user:
            session["usuario"] = user["nombre"]
            session["tipo"] = user["tipo"]
            return redirect("/admin" if user["tipo"] == "admin" else "/usuario")
        else:
            return render_template("login.html", error="Usuario o contraseña incorrecta")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

from modules.presupuesto import calcular_resumen_presupuesto

@app.route("/admin")
def admin_dashboard():
    if "usuario" not in session or session["tipo"] != "admin":
        return redirect("/login")

    resumen = calcular_resumen_presupuesto()
    return render_template(
        "admin_dashboard.html",
        usuario=session["usuario"],
        resumen=resumen
    )

@app.route("/usuario")
def user_dashboard():
    if "usuario" not in session or session["tipo"] != "usuario":
        return redirect("/login")

    return render_template(
        "user_dashboard.html",
        usuario=session["usuario"]
    )

from datetime import datetime

@app.context_processor
def inject_now():
    return {'now': datetime.now}


if __name__ == "__main__":
    socketio.run(app, debug=True)
