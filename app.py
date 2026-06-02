from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)

def inicializar_db():
    conn = sqlite3.connect('datos.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jugadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            posicion TEXT,
            resultado REAL,
            nivel TEXT,
            fecha TEXT DEFAULT (datetime('now','localtime'))
        )
    ''')
    conn.commit()
    conn.close()

def guardar_datos(nombre, posicion, resultado, nivel):
    conn = sqlite3.connect('datos.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO jugadores (nombre, posicion, resultado, nivel) VALUES (?, ?, ?, ?)",
        (nombre, posicion, resultado, nivel)
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

        preguntas = []
        for i in range(1, 9):
            valor = float(request.form.get(f"q{i}", 1))
            valor = max(1, min(5, valor))
            preguntas.append(valor)

        puntaje = sum(preguntas)
        porcentaje = round((puntaje / 40) * 100, 1)

        if porcentaje < 40:
            nivel = "BAJO"
            color = "verde"
        elif porcentaje < 70:
            nivel = "MEDIO"
            color = "amarillo"
        else:
            nivel = "ALTO"
            color = "rojo"

        recomendacion = obtener_recomendacion(porcentaje)
        guardar_datos(nombre, posicion, porcentaje, nivel)

        return render_template("index.html",
                               resultado=porcentaje,
                               nivel=nivel,
                               color=color,
                               nombre=nombre,
                               posicion=posicion,
                               recomendacion=recomendacion)
    except Exception as e:
        print("ERROR:", e)
        return render_template("index.html",
                               resultado="Error",
                               nivel="",
                               color="",
                               nombre="",
                               posicion="",
                               recomendacion=None)

@app.route("/equipo")
def ver_equipo():
    try:
        inicializar_db()
        conn = sqlite3.connect('datos.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, posicion, resultado, nivel, fecha FROM jugadores ORDER BY fecha DESC")
        datos = cursor.fetchall()
        conn.close()
        return render_template("equipo.html", datos=datos)
    except Exception as e:
        print("ERROR equipo:", e)
        return render_template("equipo.html", datos=[])

@app.route("/datos_grafico")
def datos_grafico():
    try:
        conn = sqlite3.connect('datos.db')
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, resultado, nivel FROM jugadores ORDER BY id DESC LIMIT 20")
        datos = cursor.fetchall()
        conn.close()
        return jsonify([{"nombre": d[0], "porcentaje": d[1], "nivel": d[2]} for d in datos])
    except Exception as e:
        return jsonify([])

if __name__ == "__main__":
    inicializar_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
