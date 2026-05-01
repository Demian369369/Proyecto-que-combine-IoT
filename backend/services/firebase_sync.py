"""
Sincronizacion opcional con Firebase Realtime Database.
Si FIREBASE_CREDENTIALS y FIREBASE_DB_URL no estan configurados, este modulo
simplemente no hace nada (modo solo local).
"""

import os
from flask import current_app

_firebase_app = None


def _get_firebase():
    global _firebase_app
    if _firebase_app:
        return _firebase_app

    cred_path = current_app.config.get("FIREBASE_CREDENTIALS", "")
    db_url    = current_app.config.get("FIREBASE_DB_URL", "")

    if not cred_path or not db_url:
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials, db as firebase_db

        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {"databaseURL": db_url})

        _firebase_app = firebase_db
        return _firebase_app

    except ImportError:
        # firebase-admin no instalado - modo local
        return None
    except Exception as e:
        print("Firebase init error:", e)
        return None


def push_to_firebase(reading_dict: dict):
    """
    Escribe la lectura en /readings/{device_id}/latest y
    agrega una entrada en /readings/{device_id}/history.
    """
    fb = _get_firebase()
    if fb is None:
        return

    device_id = reading_dict.get("device_id", "unknown")
    ref = fb.reference(f"readings/{device_id}")
    ref.child("latest").set(reading_dict)
    ref.child("history").push(reading_dict)
