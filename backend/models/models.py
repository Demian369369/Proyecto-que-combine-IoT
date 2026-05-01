"""
Modelos SQLAlchemy - base de datos local SQLite
"""

from datetime import datetime, timezone
from .extensions import db


class SensorReading(db.Model):
    """Lectura cruda del sensor DHT11."""
    __tablename__ = "sensor_readings"

    id          = db.Column(db.Integer, primary_key=True)
    device_id   = db.Column(db.String(64), nullable=False, index=True)
    temperature = db.Column(db.Float, nullable=False)      # grados Celsius
    humidity    = db.Column(db.Float, nullable=False)      # porcentaje
    heat_index  = db.Column(db.Float, nullable=True)
    comfort     = db.Column(db.String(32), nullable=True)  # etiqueta de confort
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id":          self.id,
            "device_id":   self.device_id,
            "temperature": self.temperature,
            "humidity":    self.humidity,
            "heat_index":  self.heat_index,
            "comfort":     self.comfort,
            "created_at":  self.created_at.isoformat(),
        }


class Alert(db.Model):
    """Alertas generadas automaticamente por el sistema de IA o umbrales."""
    __tablename__ = "alerts"

    id          = db.Column(db.Integer, primary_key=True)
    device_id   = db.Column(db.String(64), nullable=False)
    level       = db.Column(db.String(16), nullable=False)   # info | warning | critical
    message     = db.Column(db.Text, nullable=False)
    temperature = db.Column(db.Float, nullable=True)
    humidity    = db.Column(db.Float, nullable=True)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    acknowledged= db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id":           self.id,
            "device_id":    self.device_id,
            "level":        self.level,
            "message":      self.message,
            "temperature":  self.temperature,
            "humidity":     self.humidity,
            "created_at":   self.created_at.isoformat(),
            "acknowledged": self.acknowledged,
        }


class Prediction(db.Model):
    """Predicciones generadas por el modelo LSTM."""
    __tablename__ = "predictions"

    id                   = db.Column(db.Integer, primary_key=True)
    device_id            = db.Column(db.String(64), nullable=False)
    predicted_temperature= db.Column(db.Float, nullable=False)
    predicted_humidity   = db.Column(db.Float, nullable=False)
    horizon_minutes      = db.Column(db.Integer, default=30)   # minutos hacia el futuro
    confidence           = db.Column(db.Float, nullable=True)   # 0-1
    created_at           = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id":                    self.id,
            "device_id":             self.device_id,
            "predicted_temperature": self.predicted_temperature,
            "predicted_humidity":    self.predicted_humidity,
            "horizon_minutes":       self.horizon_minutes,
            "confidence":            self.confidence,
            "created_at":            self.created_at.isoformat(),
        }
