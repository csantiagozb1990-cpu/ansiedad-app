from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
import joblib
import numpy as np

app = Flask(__name__)
app.secret_key = "ansiedad2025"

PASSWORD_ADMIN = "vergel2025"

try:
    modelo = joblib.load("modelo.pkl")
    print("Modelo cargado correctamente")
except Exception as e:
    modelo = None
    print("Error cargando modelo:", e)

def inicializar_db():
    conn = sqlite3.connect('datos.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jugadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            posicion TEXT,
            equipo TEXT,
            resultado REAL,
            nivel TEXT,
            fecha TEXT DEFAULT (datetime('now','localtime'))
        )
    ''')
    conn.commit()
    conn.close()

def guardar_datos(nombre, posicion, equipo, resultado, nivel):
    conn = sqlite3.connect('datos.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO jugadores (nombre, posicion, equipo, resultado, nivel) VALUES (?, ?, ?, ?, ?)",
        (nombre, posicion, equipo, resultado, nivel)
    )
    conn.commit()
    conn.close()

def obtener_recomendacion(porcentaje):
    if porcentaje < 40:
        return {
            "titulo": "Ansiedad Baja — ¡Estás listo!",
            "texto": "Tu nivel de activación es óptimo. Mantén tu rutina de calentamiento habitual, confía en tu preparación y enfócate en disfrutar el partido.",
            "tips": [
                "Realiza tu calentamiento normal",
                "Visualiza jugadas positivas por 2 minutos",
                "Habla con tus compañeros y mantén buen ambiente"
            ]
        }
    elif porcentaje < 70:
        return {
            "titulo": "Ansiedad Media — Maneja la presión",
            "texto": "Sientes algo de presión, lo cual es normal y puede ayudarte a rendir mejor. Usa estas técnicas para canalizarla positivamente.",
            "tips": [
                "Respira profundo: inhala 4 segundos, exhala 6 segundos",
                "Repite una frase motivadora que uses habitualmente",
                "Enfócate solo en el primer minuto del partido, no en el resultado final"
            ]
        }
    else:
        return {
            "titulo": "Ansiedad Alta — Necesitas calmarte",
            "texto": "Tu nivel de ansiedad es elevado. Es importante que uses técnicas de relajación antes del partido para recuperar el control.",
            "tips": [
                "Haz 5 respiraciones lentas y profundas ahora mismo",
                "Sacude las manos y los brazos para liberar tensión muscular",
                "Habla con el preparador físico o psicólogo del equipo",
                "Recuerda un partido anterior en que jugaste muy bien"
            ]
        }

@app.route("/")
def home():
    inicializar_db()
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        nombre = request.form.get("nombre", "Jugador").strip()
        posicion = request.form.get("posicion", "").strip()
        equipo = request.form.get("equipo", "").strip()

        q12 = float(request.form.get("q12", 3))
        q15 = float(request.form.get("q15", 3))
        q18 = float(request.form.get("q18", 3))
        q30 = float(request.form.get("q30", 3))
        q31 = float(request.form.get("q31", 3))
        q22 = float(request.form.get("q22", 3))
        q28 = float(request.form.get("q28", 3))
        q14 = float(request.form.get("q14", 3))
        q17 = float(request.form.get("q17", 3))
        q24 = float(request.form.get("q24", 3))

        preguntas_ansiedad = [q12, q15, q18, q30, q31, q22, q28]
        preguntas_confianza = [q14, q17, q24]
        suma_ansiedad = sum(preguntas_ansiedad)
        suma_confianza = sum(preguntas_confianza)
        porcentaje = round(((suma_ansiedad / 35) * 70 + ((15 - suma_confianza) / 15) * 30), 1)
        porcentaje = max(0, min(100, porcentaje))

        if modelo:
            try:
                features = np.array([[q12, q15, q18, q30, q31, q22, q28, q14, q17, q24]])
                pred = modelo.predict(features)[0]
                nivel = pred
                if nivel == "BAJO":
                    porcentaje = min(porcentaje, 39)
                elif nivel == "MEDIO":
                    porcentaje = max(40, min(porcentaje, 69))
                else:
                    porcentaje = max(70, porcentaje)
            except Exception as e:
                print("Error modelo:", e)
                if porcentaje < 40: nivel = "BAJO"
                elif porcentaje < 70: nivel = "MEDIO"
                else: nivel = "ALTO"
        else:
            if porcentaje < 40: nivel = "BAJO"
            elif porcentaje < 70: nivel = "MEDIO"
            else: nivel = "ALTO"

        if nivel == "BAJO": color = "verde"
        elif nivel == "MEDIO": color = "amarillo"
        else: color = "rojo"

        recomendacion = obtener_recomendacion(porcentaje)
        guardar_datos(nombre, posicion, equipo, porcentaje, nivel)

        return render_template("index.html",
                               resultado=porcentaje,
                               nivel=nivel,
                               color=color,
                               nombre=nombre,
                               posicion=posicion,
                               equipo=equipo,
                               recomendacion=recomendacion)
    except Exception as e:
        print("ERROR:", e)
        return render_template("index.html",
                               resultado="Error",
                               nivel="", color="",
                               nombre="", posicion="", equipo="",
                               recomendacion=None)

# --- LOGIN ADMIN ---
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == PASSWORD_ADMIN:
            session["admin"] = True
            return redirect(url_for("dashboard_general"))
        else:
            error = "Contraseña incorrecta"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

# --- DASHBOARD GENERAL ---
@app.route("/dashboard")
def dashboard_general():
    if not session.get("admin"):
        return redirect(url_for("login"))
    try:
        inicializar_db()
        conn = sqlite3.connect('datos.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, posicion, equipo, resultado, nivel, fecha FROM jugadores ORDER BY fecha DESC")
        todos = cursor.fetchall()
        cursor.execute("SELECT equipo, AVG(resultado), COUNT(*) FROM jugadores GROUP BY equipo")
        por_equipo = cursor.fetchall()
        conn.close()
        return render_template("dashboard.html", todos=todos, por_equipo=por_equipo)
    except Exception as e:
        print("ERROR dashboard:", e)
        return render_template("dashboard.html", todos=[], por_equipo=[])

# --- DASHBOARD POR EQUIPO ---
@app.route("/equipo/<nombre_equipo>")
def dashboard_equipo(nombre_equipo):
    if not session.get("admin"):
        return redirect(url_for("login"))
    try:
        conn = sqlite3.connect('datos.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, posicion, resultado, nivel, fecha FROM jugadores WHERE equipo=? ORDER BY fecha DESC", (nombre_equipo,))
        datos = cursor.fetchall()
        conn.close()
        return render_template("equipo.html", datos=datos, nombre_equipo=nombre_equipo)
    except Exception as e:
        print("ERROR equipo:", e)
        return render_template("equipo.html", datos=[], nombre_equipo=nombre_equipo)

if __name__ == "__main__":
    inicializar_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
