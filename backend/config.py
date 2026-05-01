"""
Configuracion por entorno.
Copia .env.example a .env y rellena los valores antes de ejecutar.
"""

import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    SECRET_KEY              = os.getenv("SECRET_KEY", "cambia-esta-clave")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Firebase (opcional - solo si usas sincronizacion en la nube)
    FIREBASE_CREDENTIALS    = os.getenv("FIREBASE_CREDENTIALS", "")   # ruta al JSON
    FIREBASE_DB_URL         = os.getenv("FIREBASE_DB_URL", "")        # https://xxx.firebaseio.com

    # Umbral de alerta de temperatura
    TEMP_ALERT_THRESHOLD    = float(os.getenv("TEMP_ALERT_THRESHOLD", "30.0"))
    HUMIDITY_ALERT_HIGH     = float(os.getenv("HUMIDITY_ALERT_HIGH", "80.0"))
    HUMIDITY_ALERT_LOW      = float(os.getenv("HUMIDITY_ALERT_LOW", "20.0"))


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, '..', 'data', 'airsense.db')}"


class ProductionConfig(BaseConfig):
    DEBUG = False
    # Sustituir por PostgreSQL o MySQL en produccion
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, '..', 'data', 'airsense.db')}"
    )


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
