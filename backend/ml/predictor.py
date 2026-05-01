"""
AirSense ML - Predictor LSTM
Entrena con datos historicos de SQLite y predice temperatura/humedad
para los proximos N minutos.

Uso:
    python -m backend.ml.predictor --train       # entrena y guarda el modelo
    python -m backend.ml.predictor --predict     # muestra ultima prediccion
"""

import os
import argparse
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), "airsense_lstm.keras")
SEQUENCE_LEN = 20      # lecturas historicas que ve el modelo
HORIZON_MIN  = 30      # minutos hacia el futuro
MIN_SAMPLES  = 50      # minimo de datos para entrenar/predecir


def _load_data_from_db(device_id=None):
    """Carga lecturas de SQLite via SQLAlchemy (requiere contexto Flask)."""
    from ..models.models import SensorReading
    from sqlalchemy import desc

    q = SensorReading.query.order_by(desc(SensorReading.created_at))
    if device_id:
        q = q.filter_by(device_id=device_id)
    rows = q.limit(5000).all()
    rows.reverse()   # orden cronologico

    temps = np.array([r.temperature for r in rows], dtype=np.float32)
    hums  = np.array([r.humidity    for r in rows], dtype=np.float32)
    return temps, hums


def _build_sequences(temps, hums, seq_len=SEQUENCE_LEN):
    """Construye X (secuencias) e y (siguiente valor) para el LSTM."""
    X, y = [], []
    data = np.stack([temps, hums], axis=1)   # (N, 2)
    for i in range(len(data) - seq_len):
        X.append(data[i : i + seq_len])
        y.append(data[i + seq_len])
    return np.array(X), np.array(y)


def _normalize(arr):
    mu  = arr.mean(axis=0)
    std = arr.std(axis=0) + 1e-8
    return (arr - mu) / std, mu, std


def train(device_id=None):
    """Entrena el modelo LSTM y lo guarda en MODEL_PATH."""
    try:
        import tensorflow as tf
        from tensorflow import keras
    except ImportError:
        print("TensorFlow no instalado. Ejecuta: pip install tensorflow")
        return False

    temps, hums = _load_data_from_db(device_id)
    if len(temps) < MIN_SAMPLES:
        print(f"Datos insuficientes ({len(temps)} < {MIN_SAMPLES}). Sigue recolectando.")
        return False

    X, y = _build_sequences(temps, hums)

    # Normalizar
    X_flat = X.reshape(-1, 2)
    _, mu, std = _normalize(X_flat)
    X_norm = (X - mu) / std
    y_norm = (y - mu) / std

    # Separar train/val (80/20)
    split    = int(len(X_norm) * 0.8)
    X_train  = X_norm[:split]
    X_val    = X_norm[split:]
    y_train  = y_norm[:split]
    y_val    = y_norm[split:]

    # Arquitectura LSTM
    model = keras.Sequential([
        keras.layers.LSTM(64, return_sequences=True,
                          input_shape=(SEQUENCE_LEN, 2)),
        keras.layers.Dropout(0.2),
        keras.layers.LSTM(32),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(16, activation="relu"),
        keras.layers.Dense(2),          # [temperatura, humedad]
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(1e-3),
        loss="mse",
        metrics=["mae"],
    )

    callbacks = [
        keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=5, verbose=1),
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=100,
        batch_size=32,
        callbacks=callbacks,
        verbose=1,
    )

    model.save(MODEL_PATH)

    # Guardar parametros de normalizacion junto al modelo
    np.save(MODEL_PATH.replace(".keras", "_norm.npy"),
            np.array([mu, std]))

    val_mae = min(history.history["val_mae"])
    print(f"Modelo guardado. MAE validacion: {val_mae:.4f}")
    return True


def run_prediction(device_id=None):
    """
    Carga el modelo y devuelve la prediccion para los proximos HORIZON_MIN minutos.
    Retorna dict con keys: temperature, humidity, horizon_minutes, confidence
    Si el modelo no existe aun, retorna None (silenciosamente).
    """
    if not os.path.exists(MODEL_PATH):
        return None

    norm_path = MODEL_PATH.replace(".keras", "_norm.npy")
    if not os.path.exists(norm_path):
        return None

    try:
        import tensorflow as tf
        from tensorflow import keras
    except ImportError:
        return None

    try:
        model    = keras.models.load_model(MODEL_PATH)
        norm_arr = np.load(norm_path)
        mu, std  = norm_arr[0], norm_arr[1]

        temps, hums = _load_data_from_db(device_id)
        if len(temps) < SEQUENCE_LEN:
            return None

        seq  = np.stack([temps[-SEQUENCE_LEN:], hums[-SEQUENCE_LEN:]], axis=1)
        seq_norm = (seq - mu) / std
        X    = seq_norm[np.newaxis, ...]    # (1, seq_len, 2)

        y_norm = model.predict(X, verbose=0)[0]
        y_pred = y_norm * std + mu

        # Confianza aproximada: inverso del MAE reciente sobre los ultimos 10
        if len(temps) >= SEQUENCE_LEN + 10:
            errors = []
            for i in range(10):
                idx = -(SEQUENCE_LEN + 10 - i)
                s   = np.stack([temps[idx:idx+SEQUENCE_LEN],
                                hums[idx:idx+SEQUENCE_LEN]], axis=1)
                s_n = (s - mu) / std
                p   = model.predict(s_n[np.newaxis], verbose=0)[0]
                p_  = p * std + mu
                errors.append(abs(p_[0] - temps[idx + SEQUENCE_LEN]))
            mae        = np.mean(errors)
            confidence = float(max(0, 1 - mae / 10))
        else:
            confidence = None

        return {
            "temperature":     round(float(y_pred[0]), 2),
            "humidity":        round(float(y_pred[1]), 2),
            "horizon_minutes": HORIZON_MIN,
            "confidence":      round(confidence, 3) if confidence is not None else None,
        }

    except Exception as e:
        print("Error en prediccion:", e)
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train",   action="store_true")
    parser.add_argument("--predict", action="store_true")
    parser.add_argument("--device",  default=None)
    args = parser.parse_args()

    # Se necesita contexto Flask para acceder a la BD
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from backend import create_app
    app = create_app()

    with app.app_context():
        if args.train:
            train(args.device)
        elif args.predict:
            result = run_prediction(args.device)
            print(result)
        else:
            parser.print_help()
