"""
Rutas REST /api/* - consumidas por el dashboard web
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import func, desc
from ..extensions import db
from ..models.models import SensorReading, Alert, Prediction

api_bp = Blueprint("api", __name__)


# ── Lecturas ───────────────────────────────────────────────────────────────

@api_bp.route("/api/readings", methods=["GET"])
def get_readings():
    device_id = request.args.get("device_id")
    limit     = min(int(request.args.get("limit", 100)), 1000)
    hours     = int(request.args.get("hours", 24))

    from datetime import datetime, timezone, timedelta
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    q = SensorReading.query.filter(SensorReading.created_at >= since)
    if device_id:
        q = q.filter_by(device_id=device_id)
    q = q.order_by(desc(SensorReading.created_at)).limit(limit)

    return jsonify([r.to_dict() for r in q.all()])


@api_bp.route("/api/readings/latest", methods=["GET"])
def get_latest():
    device_id = request.args.get("device_id")
    q = SensorReading.query
    if device_id:
        q = q.filter_by(device_id=device_id)
    reading = q.order_by(desc(SensorReading.created_at)).first()
    if not reading:
        return jsonify({"error": "Sin datos"}), 404
    return jsonify(reading.to_dict())


@api_bp.route("/api/readings/stats", methods=["GET"])
def get_stats():
    """Estadisticas de las ultimas N horas."""
    hours  = int(request.args.get("hours", 24))
    device = request.args.get("device_id")

    from datetime import datetime, timezone, timedelta
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    q = SensorReading.query.filter(SensorReading.created_at >= since)
    if device:
        q = q.filter_by(device_id=device)

    result = q.with_entities(
        func.avg(SensorReading.temperature).label("avg_temp"),
        func.min(SensorReading.temperature).label("min_temp"),
        func.max(SensorReading.temperature).label("max_temp"),
        func.avg(SensorReading.humidity).label("avg_hum"),
        func.min(SensorReading.humidity).label("min_hum"),
        func.max(SensorReading.humidity).label("max_hum"),
        func.count(SensorReading.id).label("count"),
    ).one()

    return jsonify({
        "hours":    hours,
        "count":    result.count,
        "temperature": {
            "avg": round(result.avg_temp or 0, 2),
            "min": round(result.min_temp or 0, 2),
            "max": round(result.max_temp or 0, 2),
        },
        "humidity": {
            "avg": round(result.avg_hum or 0, 2),
            "min": round(result.min_hum or 0, 2),
            "max": round(result.max_hum or 0, 2),
        },
    })


# ── Alertas ────────────────────────────────────────────────────────────────

@api_bp.route("/api/alerts", methods=["GET"])
def get_alerts():
    only_active = request.args.get("active", "true").lower() == "true"
    q = Alert.query
    if only_active:
        q = q.filter_by(acknowledged=False)
    return jsonify([a.to_dict() for a in q.order_by(desc(Alert.created_at)).limit(50).all()])


@api_bp.route("/api/alerts/<int:alert_id>/ack", methods=["POST"])
def acknowledge_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.acknowledged = True
    db.session.commit()
    return jsonify({"status": "acknowledged"})


# ── Predicciones ───────────────────────────────────────────────────────────

@api_bp.route("/api/predictions/latest", methods=["GET"])
def get_latest_prediction():
    device_id = request.args.get("device_id")
    q = Prediction.query
    if device_id:
        q = q.filter_by(device_id=device_id)
    pred = q.order_by(desc(Prediction.created_at)).first()
    if not pred:
        return jsonify({"error": "Sin predicciones aun"}), 404
    return jsonify(pred.to_dict())


# ── Dispositivos registrados ───────────────────────────────────────────────

@api_bp.route("/api/devices", methods=["GET"])
def get_devices():
    devices = db.session.query(
        SensorReading.device_id,
        func.count(SensorReading.id).label("total_readings"),
        func.max(SensorReading.created_at).label("last_seen"),
    ).group_by(SensorReading.device_id).all()

    return jsonify([
        {
            "device_id":      d.device_id,
            "total_readings": d.total_readings,
            "last_seen":      d.last_seen.isoformat() if d.last_seen else None,
        }
        for d in devices
    ])
