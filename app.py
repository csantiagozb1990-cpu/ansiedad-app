from flask import Flask, render_template, request
import joblib
import numpy as np
import sqlite3

app = Flask(__name__)

# ✅ cargar modelo
try:
    modelo = joblib.load("modelo.pkl")
except:
    modelo = None


# ✅ guardar datos
def guardar_datos(nombre, resultado):
    conn = sqlite3.connect('datos.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS jugadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        resultado REAL
    )
    ''')

    cursor.execute("INSERT INTO jugadores (nombre, resultado) VALUES (?, ?)", 
                   (nombre, resultado))

    conn.commit()
    conn.close()


# ✅ PAGINA PRINCIPAL
@app.route("/")
def home():
    return render_template("index.html")


# ✅ HISTORIAL DE JUGADORES (LO NUEVO)
@app.route("/jugadores")
def ver_jugadores():
    conn = sqlite3.connect('datos.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jugadores")
    datos = cursor.fetchall()

    conn.close()

    return render_template("jugadores.html", datos=datos)


# ✅ PREDICCIÓN
@app.route("/predict", methods=["POST"])
def predict():
    try:
        nombre = request.form.get("nombre")

        q1 = float(request.form.get("q1", 0))
        q2 = float(request.form.get("q2", 0))
        q3 = float(request.form.get("q3", 0))
        q4 = float(request.form.get("q4", 0))
        q5 = float(request.form.get("q5", 0))
        q6 = float(request.form.get("q6", 0))
        q7 = float(request.form.get("q7", 0))
        q8 = float(request.form.get("q8", 0))

        datos = [q1, q2, q3, q4, q5, q6, q7, q8]

        # completar para modelo Orange
        while len(datos) < 20:
            datos.append(0)

        datos = np.array([datos])

        # predicción
        if modelo:
            try:
                prob = modelo.predict_proba(datos)
                porcentaje = round(prob[0][1] * 100, 2)
            except:
                porcentaje = (sum(datos[:8]) / 40) * 100
        else:
            porcentaje = (sum(datos[:8]) / 40) * 100

        # nivel
        if porcentaje < 40:
            nivel = "BAJO 🟢"
        elif porcentaje < 70:
            nivel = "MEDIO 🟡"
        else:
            nivel = "ALTO 🔴"

        # ✅ guardar datos
        guardar_datos(nombre, porcentaje)

        return render_template("index.html",
                               resultado=porcentaje,
                               nivel=nivel,
                               nombre=nombre)

    except Exception as e:
        print("ERROR:", e)

        return render_template("index.html",
                               resultado="Error",
                               nivel="Error del sistema")


# ✅ necesario para Render
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
