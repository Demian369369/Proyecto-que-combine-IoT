"""
Punto de entrada del servidor.
Ejecutar: python run.py
"""

import os
from backend import create_app

env = os.getenv("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    # Crear directorio de datos si no existe
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=(env == "development"))
