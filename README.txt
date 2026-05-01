AirSense - Sistema IoT + IA de Monitoreo Ambiental
==================================================

Proyecto academico: Programacion Internet 
Universidad de Guadalajara - CUCEI
Alumnos: Ragknos Demian Fernandez Agraz Rodriguez 
Sensores: DHT11 (temperatura y humedad) / ESP32 via MicroPython


DESCRIPCION GENERAL
-------------------
AirSense conecta un sensor DHT11 en un ESP32 a un servidor Flask local que
almacena las lecturas en SQLite, las sincroniza opcionalmente con Firebase y
ejecuta un modelo LSTM de TensorFlow para predecir la temperatura y humedad
de los proximos 30 minutos. Un dashboard web en tiempo real muestra las
lecturas, graficas historicas, predicciones del modelo y alertas automaticas.


ARQUITECTURA DEL SISTEMA
------------------------

  [DHT11]
     |
  [ESP32 MicroPython]  --WiFi-HTTP POST-->  [Flask Backend]
                                                   |
                                            -------+-------
                                            |             |
                                        [SQLite]    [Firebase]
                                            |        (opcional)
                                     [ML Predictor]
                                       (TF LSTM)
                                            |
                                     [Dashboard Web]
                                      (HTML/JS/Chart.js)


ESTRUCTURA DE ARCHIVOS
----------------------

air-monitor/
|-- esp32/
|   |-- main.py                 Firmware MicroPython del ESP32
|
|-- backend/
|   |-- __init__.py             Flask app factory
|   |-- config.py               Configuracion por entorno
|   |-- extensions.py           SQLAlchemy, CORS (singletons)
|   |-- models/
|   |   |-- models.py           Modelos ORM: SensorReading, Alert, Prediction
|   |-- routes/
|   |   |-- ingest.py           POST /api/ingest  (recibe datos del ESP32)
|   |   |-- api.py              GET /api/*        (consumido por el dashboard)
|   |   |-- web.py              GET /             (sirve el dashboard HTML)
|   |-- ml/
|   |   |-- predictor.py        Modelo LSTM: entrenamiento e inferencia
|   |   |-- airsense_lstm.keras Archivo del modelo (generado al entrenar)
|   |   |-- airsense_lstm_norm.npy  Parametros de normalizacion
|   |-- services/
|       |-- firebase_sync.py    Sincronizacion Firebase Realtime Database
|
|-- web/
|   |-- templates/
|       |-- index.html          Dashboard HTML (Chart.js, JS puro)
|
|-- data/
|   |-- airsense.db             Base de datos SQLite (generada en ejecucion)
|
|-- run.py                      Punto de entrada del servidor
|-- seed_data.py                Generador de datos de prueba
|-- requirements.txt            Dependencias Python
|-- .env.example                Plantilla de variables de entorno
|-- README.txt                  Este archivo


BASE DE DATOS SQL - ESQUEMA
---------------------------

Tabla sensor_readings:
  id           INTEGER    PRIMARY KEY
  device_id    TEXT       identificador del ESP32
  temperature  REAL       grados Celsius (DHT11)
  humidity     REAL       porcentaje relativo
  heat_index   REAL       indice de calor calculado
  comfort      TEXT       etiqueta: frio, confortable, moderado, seco, etc.
  created_at   DATETIME   timestamp UTC automatico

Tabla alerts:
  id           INTEGER    PRIMARY KEY
  device_id    TEXT
  level        TEXT       info | warning | critical
  message      TEXT       descripcion legible
  temperature  REAL       valor al momento de la alerta
  humidity     REAL
  created_at   DATETIME
  acknowledged BOOLEAN    true cuando el operador confirma la alerta

Tabla predictions:
  id                    INTEGER  PRIMARY KEY
  device_id             TEXT
  predicted_temperature REAL     temperatura predicha
  predicted_humidity    REAL     humedad predicha
  horizon_minutes       INTEGER  horizonte de prediccion (default 30)
  confidence            REAL     0.0 a 1.0
  created_at            DATETIME


ENDPOINTS REST
--------------

POST /api/ingest
  Body JSON: { device_id, temperature, humidity, heat_index?, comfort? }
  Respuesta: { status, reading_id, alerts }

GET  /api/readings?device_id=&hours=24&limit=100
GET  /api/readings/latest?device_id=
GET  /api/readings/stats?hours=24&device_id=
GET  /api/alerts?active=true
POST /api/alerts/<id>/ack
GET  /api/predictions/latest?device_id=
GET  /api/devices
GET  /   (dashboard HTML)


MODELO DE IA - LSTM
-------------------
Arquitectura:
  Input  -> LSTM(64, return_sequences=True)
          -> Dropout(0.2)
          -> LSTM(32)
          -> Dropout(0.2)
          -> Dense(16, relu)
          -> Dense(2)   [temperatura, humedad]

Entrada:  secuencia de 20 lecturas consecutivas (normalizadas)
Salida:   siguiente valor de [temperatura, humedad]
Horizonte: 30 minutos aprox. (dependiendo del intervalo de lectura)
Entrenamiento: EarlyStopping + ReduceLROnPlateau, hasta 100 epocas

El modelo requiere al menos 50 lecturas previas para entrenar.
Con menos datos, el endpoint de prediccion devuelve null y el
dashboard muestra "entrenando..."


INSTALACION Y EJECUCION
-----------------------

1. Instalar dependencias:
   pip install -r requirements.txt

2. Crear archivo .env:
   cp .env.example .env
   (edita los valores segun tu entorno)

3. Crear directorio de datos:
   mkdir data

4. Arrancar el servidor:
   python run.py
   (acceder a http://localhost:5000)

5. Flashear el ESP32:
   - Abrir esp32/main.py en Thonny IDE
   - Cambiar WIFI_SSID, WIFI_PASSWORD y BACKEND_URL
   - Cargar al ESP32 como main.py

6. Generar datos de prueba (sin ESP32):
   python seed_data.py

7. Entrenar el modelo IA (requiere >= 50 lecturas):
   python -m backend.ml.predictor --train

8. Ver prediccion actual:
   python -m backend.ml.predictor --predict


FIREBASE (OPCIONAL)
-------------------
1. Crear proyecto en https://console.firebase.google.com
2. Activar Realtime Database
3. Ir a Configuracion -> Cuentas de servicio -> Generar nueva clave privada
4. Guardar el JSON descargado como firebase-credentials.json en la raiz
5. Completar FIREBASE_CREDENTIALS y FIREBASE_DB_URL en .env

Sin Firebase el sistema funciona completamente en modo local (SQLite).


DEPENDENCIAS PRINCIPALES
------------------------
flask 3.0         Web framework
flask-sqlalchemy  ORM para SQLite
flask-cors        CORS para la API
tensorflow 2.16   Modelo LSTM
numpy             Algebra lineal
firebase-admin    Sincronizacion en la nube (opcional)
chart.js 4.4      Graficas en el navegador (CDN)


FLUJO DE DATOS
--------------
1. DHT11 mide temperatura y humedad cada 10 s
2. ESP32 calcula indice de calor y etiqueta de confort
3. ESP32 envia POST /api/ingest al servidor Flask via WiFi
4. Flask guarda en SQLite, genera alertas si hay umbrales superados
5. Flask llama al predictor LSTM con las ultimas 20 lecturas
6. La prediccion se guarda en la tabla predictions
7. Flask sincroniza la lectura con Firebase (si esta configurado)
8. El dashboard web solicita /api/* cada 10 s y actualiza las graficas
