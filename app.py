from flask import Flask, render_template, request
import joblib
import numpy as np

app = Flask(__name__)

# cargar modelo
try:
    modelo = joblib.load("modelo.pkl")
except:
    modelo = None

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        q1 = float(request.form.get("q1", 0))
        q2 = float(request.form.get("q2", 0))
        q3 = float(request.form.get("q3", 0))

        datos = [q1, q2, q3]

        # completar entrada
        while len(datos) < 20:
            datos.append(0)

        datos = np.array([datos])

        if modelo:
            try:
                pred = modelo.predict(datos)

                if hasattr(modelo, "predict_proba"):
                    prob = modelo.predict_proba(datos)
                    porcentaje = round(prob[0][1] * 100, 2)
                else:
                    porcentaje = 70 if pred[0] == 1 else 30

            except:
                # fallback si el modelo falla
                porcentaje = (q1 + q2 + q3) / 15 * 100

        else:
            # fallback total
            porcentaje = (q1 + q2 + q3) / 15 * 100

        # nivel
        if porcentaje < 40:
            nivel = "BAJO 🟢"
        elif porcentaje < 70:
            nivel = "MEDIO 🟡"
        else:
            nivel = "ALTO 🔴"

        return render_template("index.html",
                               resultado=round(porcentaje, 2),
                               nivel=nivel)

    except Exception as e:
        print("ERROR REAL:", e)
        return render_template("index.html",
                               resultado="Error",
                               nivel="Revisa datos")

if __name__ == "__main__":
    print("🚀 IA DE ANSIEDAD INICIADA")
    app.run(host="0.0.0.0", port=5000, debug=True)