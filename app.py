from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
import joblib
import numpy as np
import requests as req_http

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
    try:
        cursor.execute("ALTER TABLE jugadores ADD COLUMN equipo TEXT")
    except:
        pass
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
            "tips": ["Realiza tu calentamiento normal", "Visualiza jugadas positivas por 2 minutos", "Habla con tus compañeros y mantén buen ambiente"]
        }
    elif porcentaje < 70:
        return {
            "titulo": "Ansiedad Media — Maneja la presión",
            "texto": "Sientes algo de presión, lo cual es normal y puede ayudarte a rendir mejor. Usa estas técnicas para canalizarla positivamente.",
            "tips": ["Respira profundo: inhala 4 segundos, exhala 6 segundos", "Repite una frase motivadora que uses habitualmente", "Enfócate solo en el primer minuto del partido, no en el resultado final"]
        }
    else:
        return {
            "titulo": "Ansiedad Alta — Necesitas calmarte",
            "texto": "Tu nivel de ansiedad es elevado. Es importante que uses técnicas de relajación antes del partido para recuperar el control.",
            "tips": ["Haz 5 respiraciones lentas y profundas ahora mismo", "Sacude las manos y los brazos para liberar tensión muscular", "Habla con el preparador físico o psicólogo del equipo", "Recuerda un partido anterior en que jugaste muy bien"]
        }

@app.route("/")
def home():
    inicializar_db()
    return render_template("index.html", resultado=None, jugador_id=None, nivel=None, color=None, nombre=None, posicion=None, equipo=None, recomendacion=None)

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

        suma_ansiedad = q12 + q15 + q18 + q30 + q31 + q22 + q28
        suma_confianza = q14 + q17 + q24
        porcentaje = round(((suma_ansiedad / 35) * 70 + ((15 - suma_confianza) / 15) * 30), 1)
        porcentaje = max(0, min(100, porcentaje))

        if modelo:
            try:
                features = np.array([[q12, q15, q18, q30, q31, q22, q28, q14, q17, q24]])
                pred = modelo.predict(features)[0]
                nivel = pred
                if nivel == "BAJO": porcentaje = min(porcentaje, 39)
                elif nivel == "MEDIO": porcentaje = max(40, min(porcentaje, 69))
                else: porcentaje = max(70, porcentaje)
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

        conn2 = sqlite3.connect('datos.db')
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT last_insert_rowid()")
        jugador_id = cursor2.fetchone()[0]
        conn2.close()

        return render_template("index.html",
                               resultado=porcentaje,
                               nivel=nivel,
                               color=color,
                               nombre=nombre,
                               posicion=posicion,
                               equipo=equipo,
                               recomendacion=recomendacion,
                               jugador_id=jugador_id)
    except Exception as e:
        print("ERROR:", e)
        return render_template("index.html",
                               resultado=None, nivel=None, color=None,
                               nombre=None, posicion=None, equipo=None,
                               recomendacion=None, jugador_id=None)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == PASSWORD_ADMIN:
            session["admin"] = True
            return redirect(url_for("ver_equipo"))
        else:
            error = "Contraseña incorrecta"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("home"))

@app.route("/equipo")
def ver_equipo():
    try:
        inicializar_db()
        conn = sqlite3.connect('datos.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, posicion, equipo, resultado, nivel, fecha FROM jugadores ORDER BY fecha DESC")
        datos = cursor.fetchall()
        conn.close()
        return render_template("equipo.html", datos=datos)
    except Exception as e:
        print("ERROR equipo:", e)
        return render_template("equipo.html", datos=[])

@app.route("/chat/<int:jugador_id>")
def chat(jugador_id):
    try:
        inicializar_db()
        conn = sqlite3.connect('datos.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, posicion, equipo, resultado, nivel FROM jugadores WHERE id=?", (jugador_id,))
        jugador = cursor.fetchone()
        conn.close()
        if not jugador:
            return redirect(url_for('home'))
        return render_template("chat.html",
                               nombre=jugador[0],
                               posicion=jugador[1],
                               equipo=jugador[2] or "El Vergel",
                               porcentaje=jugador[3],
                               nivel=jugador[4],
                               jugador_id=jugador_id)
    except Exception as e:
        print("ERROR chat:", e)
        return redirect(url_for('home'))

@app.route("/chat_mensaje", methods=["POST"])
def chat_mensaje():
    try:
        data = request.get_json()
        nombre     = data.get("nombre", "Jugador")
        posicion   = data.get("posicion", "")
        equipo     = data.get("equipo", "El Vergel")
        porcentaje = data.get("porcentaje", 50)
        nivel      = data.get("nivel", "MEDIO")
        historial  = data.get("historial", [])
        mensaje    = data.get("mensaje", "")

        if nivel == "ALTO":
            variables = "frustración ante errores, ansiedad antes del partido y presión externa (entrenador o familia)"
        elif nivel == "MEDIO":
            variables = "nervios antes de competir y cierta presión por el rendimiento"
        else:
            variables = "buena autoconfianza y bajo nivel de presión"

        system_prompt = f"""Eres un psicólogo deportivo especializado en fútbol juvenil llamado "Ansi".
Estás hablando con {nombre}, un jugador de {posicion} del equipo {equipo}.
Acaba de completar una evaluación de ansiedad precompetitiva y obtuvo un {porcentaje}% — nivel {nivel}.
Sus factores más relevantes son: {variables}.
Tu rol es:
- Dar apoyo emocional cálido y empático
- Usar lenguaje simple, cercano y motivador, apropiado para un joven deportista de 13-17 años
- Dar tips psicológicos prácticos y concretos (respiración, visualización, rutinas, autodiálogo positivo)
- NO hacer diagnósticos clínicos ni recomendar medicamentos
- Mantener las respuestas cortas (máximo 4 oraciones) para que sean fáciles de leer
- Siempre terminar con una pregunta o invitación a continuar la conversación
- Si el jugador expresa algo muy serio (autolesión, depresión profunda), recomienda hablar con un adulto de confianza
Recuerda siempre su nombre y contexto en cada respuesta. Sé su aliado, no su terapeuta."""

        mensajes_groq = [{"role": m["role"], "content": m["content"]} for m in historial]
        mensajes_groq.append({"role": "user", "content": mensaje})

        groq_key = os.environ.get("GROQ_API_KEY", "")
        response = req_http.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "system", "content": system_prompt}] + mensajes_groq,
                "max_tokens": 300,
                "temperature": 0.7
            },
            timeout=15
        )
        texto = response.json()["choices"][0]["message"]["content"]
        return jsonify({"respuesta": texto})
    except Exception as e:
        print("ERROR chat_mensaje:", e)
        return jsonify({"respuesta": "Lo siento, tuve un problema. ¿Puedes intentarlo de nuevo?"})

if __name__ == "__main__":
    inicializar_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
