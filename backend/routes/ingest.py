"""
Ruta /api/ingest - recibe lecturas del ESP32 vía HTTP POST
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
from ..extensions import db
from ..models.models import SensorReading, Alert, Prediction
from ..ml.predictor import run_prediction
from ..services.firebase_sync import push_to_firebase

ingest_bp = Blueprint("ingest", __name__)


def _generate_alerts(device_id, t, h):
    """Crea alertas si los valores superan umbrales configurados."""
    alerts = []
    cfg = current_app.config

    if t >= cfg["TEMP_ALERT_THRESHOLD"]:
        alerts.append(Alert(
            device_id=device_id,
            level="warning" if t < cfg["TEMP_ALERT_THRESHOLD"] + 5 else "critical",
            message=f"Temperatura elevada: {t} C (umbral {cfg['TEMP_ALERT_THRESHOLD']} C)",
            temperature=t,
            humidity=h,
        ))

    if h >= cfg["HUMIDITY_ALERT_HIGH"]:
        alerts.append(Alert(
            device_id=device_id,
            level="warning",
            message=f"Humedad muy alta: {h}% (umbral {cfg['HUMIDITY_ALERT_HIGH']}%)",
            temperature=t,
            humidity=h,
        ))

    if h <= cfg["HUMIDITY_ALERT_LOW"]:
        alerts.append(Alert(
            device_id=device_id,
            level="warning",
            message=f"Ambiente muy seco: {h}% (umbral {cfg['HUMIDITY_ALERT_LOW']}%)",
            temperature=t,
            humidity=h,
        ))

    return alerts


@ingest_bp.route("/api/ingest", methods=["POST"])
def ingest():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON requerido"}), 400

    required = {"device_id", "temperature", "humidity"}
    missing  = required - set(data.keys())
    if missing:
        return jsonify({"error": f"Campos faltantes: {missing}"}), 422

    # ── Guardar lectura ────────────────────────────────────────────────────
    reading = SensorReading(
        device_id   = data["device_id"],
        temperature = float(data["temperature"]),
        humidity    = float(data["humidity"]),
        heat_index  = data.get("heat_index"),
        comfort     = data.get("comfort"),
    )
    db.session.add(reading)

    # ── Alertas por umbral ─────────────────────────────────────────────────
    alerts = _generate_alerts(reading.device_id, reading.temperature, reading.humidity)
    for a in alerts:
        db.session.add(a)

    db.session.commit()

    # ── Prediccion IA (asincrona en prod; sincrona aqui para simplicidad) ──
    prediction_result = run_prediction(reading.device_id)
    if prediction_result:
        pred = Prediction(
            device_id             = reading.device_id,
            predicted_temperature = prediction_result["temperature"],
            predicted_humidity    = prediction_result["humidity"],
            horizon_minutes       = prediction_result.get("horizon_minutes", 30),
            confidence            = prediction_result.get("confidence"),
        )
        db.session.add(pred)
        db.session.commit()

    # ── Sincronizacion Firebase (opcional, no bloquea) ─────────────────────
    try:
        push_to_firebase(reading.to_dict())
    except Exception:
        pass   # Firebase es opcional

    return jsonify({
        "status":    "ok",
        "reading_id": reading.id,
        "alerts":    len(alerts),
    }), 200
