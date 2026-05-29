# =============================================================================
# pagina_web.py - Interfaz web del Aula Inteligente - DATOS EXPANDIDOS
# Sirve datos reales de DHT11 y MQ-135 con todos los indicadores calculados.
# Se envia en dos fragmentos (CABECERA_HTML + CUERPO_HTML) para no agotar RAM.
# =============================================================================

CABECERA_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aula Inteligente - CUCEI UDEG</title>
<style>
:root{
  --fondo:#0d1117;
  --tarjeta:#161b22;
  --borde:#30363d;
  --texto:#e6edf3;
  --texto-sec:#8b949e;
  --acento:#238636;
  --acento-hover:#2ea043;
  --peligro:#da3633;
  --peligro-hover:#b62324;
  --advertencia:#e3b341;
  --info:#1f6feb;
  --info-hover:#388bfd;
  --apagado:#21262d;
}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--fondo);color:var(--texto);font-family:'Courier New',Courier,monospace;min-height:100vh;}
header{background:#010409;border-bottom:1px solid var(--borde);padding:16px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;}
header h1{font-size:1.1rem;letter-spacing:0.05em;color:var(--texto);}
header span{font-size:0.75rem;color:var(--texto-sec);}
#estado-paro{display:inline-block;width:10px;height:10px;border-radius:50%;background:#238636;margin-right:6px;vertical-align:middle;}
.contenedor{max-width:1100px;margin:0 auto;padding:24px 16px;}
h2{font-size:0.82rem;text-transform:uppercase;letter-spacing:0.1em;color:var(--texto-sec);margin-bottom:12px;border-bottom:1px solid var(--borde);padding-bottom:6px;}
h3{font-size:0.76rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--texto-sec);margin:12px 0 8px;}
.tarjeta{background:var(--tarjeta);border:1px solid var(--borde);border-radius:8px;padding:20px;margin-bottom:20px;}
.fila{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:12px;}
.fila>*{flex:1;min-width:140px;}
.metrica{background:var(--apagado);border:1px solid var(--borde);border-radius:6px;padding:12px 14px;}
.metrica .etiqueta{font-size:0.65rem;color:var(--texto-sec);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;}
.metrica .valor{font-size:1.5rem;font-weight:700;color:var(--texto);line-height:1.1;}
.metrica .unidad{font-size:0.72rem;color:var(--texto-sec);margin-left:3px;}
.metrica .sub{font-size:0.68rem;color:var(--texto-sec);margin-top:3px;}
.btn{display:inline-block;padding:10px 20px;border:none;border-radius:6px;cursor:pointer;font-family:inherit;font-size:0.85rem;font-weight:600;transition:background 0.15s,opacity 0.15s;width:100%;text-align:center;}
.btn-verde{background:var(--acento);color:#fff;}
.btn-verde:hover{background:var(--acento-hover);}
.btn-rojo{background:var(--peligro);color:#fff;}
.btn-rojo:hover{background:var(--peligro-hover);}
.btn-azul{background:var(--info);color:#fff;}
.btn-azul:hover{background:var(--info-hover);}
.btn-gris{background:var(--apagado);color:var(--texto-sec);border:1px solid var(--borde);}
.btn-gris:hover{background:#30363d;}
.btn:disabled{opacity:0.4;cursor:not-allowed;}
.modo-tabs{display:flex;gap:8px;margin-bottom:20px;}
.modo-tab{padding:8px 20px;border:1px solid var(--borde);border-radius:6px;cursor:pointer;background:var(--apagado);color:var(--texto-sec);font-family:inherit;font-size:0.8rem;font-weight:600;transition:all 0.15s;}
.modo-tab.activo{background:var(--info);border-color:var(--info);color:#fff;}
.indicador{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;background:var(--peligro);}
.indicador.on{background:#238636;}
.tabla-historial{width:100%;border-collapse:collapse;font-size:0.7rem;}
.tabla-historial th{text-align:left;padding:5px 7px;color:var(--texto-sec);border-bottom:1px solid var(--borde);text-transform:uppercase;font-size:0.62rem;letter-spacing:0.05em;white-space:nowrap;}
.tabla-historial td{padding:5px 7px;border-bottom:1px solid #21262d;color:var(--texto);white-space:nowrap;}
.tabla-historial tr:last-child td{border-bottom:none;}
.tabla-historial tr:hover td{background:#1c2128;}
.alerta-emergencia{background:#3d0d0b;border:1px solid var(--peligro);border-radius:8px;padding:14px 18px;margin-bottom:16px;font-size:0.85rem;color:#ff7b72;display:none;}
.recomendacion-box{background:#1c2128;border-left:3px solid var(--advertencia);border-radius:0 6px 6px 0;padding:10px 14px;margin-top:10px;font-size:0.78rem;color:var(--advertencia);}
.recomendacion-box.ok{border-left-color:#238636;color:#3fb950;}
.recomendacion-box.peligro{border-left-color:var(--peligro);color:#ff7b72;}
.barra-riesgo{display:flex;align-items:center;gap:8px;margin-top:6px;}
.barra-riesgo-track{flex:1;height:6px;background:#21262d;border-radius:3px;overflow:hidden;}
.barra-riesgo-fill{height:100%;border-radius:3px;transition:width 0.4s;}
.separador{height:1px;background:var(--borde);margin:16px 0;}
footer{border-top:1px solid var(--borde);padding:20px 24px;font-size:0.72rem;color:var(--texto-sec);text-align:center;line-height:1.8;}
.estado-chip{display:inline-block;padding:2px 10px;border-radius:20px;font-size:0.7rem;font-weight:600;background:var(--apagado);border:1px solid var(--borde);color:var(--texto-sec);}
.estado-chip.on{background:#0f2a18;border-color:#238636;color:#3fb950;}
.chip-modo{display:inline-block;padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:700;background:var(--info);color:#fff;margin-left:8px;}
.overflow-x{overflow-x:auto;}
</style>
</head>"""

CUERPO_HTML = """<body>
<header>
  <div>
    <span id="estado-paro"></span>
    <h1 style="display:inline;">Aula Inteligente</h1>
    <span class="chip-modo" id="chip-modo">MANUAL</span>
  </div>
  <span>CUCEI - UDEG | Programacion Para Internet</span>
</header>

<div class="contenedor">

  <div class="alerta-emergencia" id="alerta-emergencia">
    PARO DE EMERGENCIA ACTIVO - Todos los actuadores detenidos. Presione REINICIAR CIRCUITO para restaurar.
  </div>

  <!-- Selector de modo -->
  <div class="modo-tabs">
    <button class="modo-tab activo" id="tab-manual" onclick="cambiarModo('manual')">Modo Manual</button>
    <button class="modo-tab" id="tab-auto" onclick="cambiarModo('automatico')">Modo Automatico</button>
  </div>

  <!-- ================================================================
       ESCANEO AMBIENTAL - DATOS EXPANDIDOS
  ================================================================ -->
  <div class="tarjeta">
    <h2>Escaneo Ambiental - Tiempo Real</h2>

    <h3>DHT11 - Temperatura y Humedad</h3>
    <div class="fila">
      <div class="metrica">
        <div class="etiqueta">Temperatura</div>
        <div class="valor" id="val-temp">--<span class="unidad">°C</span></div>
      </div>
      <div class="metrica">
        <div class="etiqueta">Humedad Relativa</div>
        <div class="valor" id="val-hum">--<span class="unidad">%</span></div>
      </div>
      <div class="metrica">
        <div class="etiqueta">Indice de Calor</div>
        <div class="valor" id="val-ic">--<span class="unidad">°C</span></div>
        <div class="sub">Sensacion termica real</div>
      </div>
      <div class="metrica">
        <div class="etiqueta">Punto de Rocio</div>
        <div class="valor" id="val-pr">--<span class="unidad">°C</span></div>
        <div class="sub">Condensacion si baja a este valor</div>
      </div>
      <div class="metrica">
        <div class="etiqueta">Confort Termico</div>
        <div class="valor" id="val-confort" style="font-size:1rem;padding-top:4px;">--</div>
      </div>
    </div>

    <h3>MQ-135 - Calidad del Aire</h3>
    <div class="fila">
      <div class="metrica">
        <div class="etiqueta">Calidad del Aire</div>
        <div class="valor" id="val-aire">--<span class="unidad">%</span></div>
        <div class="sub">100% = aire limpio</div>
      </div>
      <div class="metrica">
        <div class="etiqueta">CO2 Estimado</div>
        <div class="valor" id="val-ppm">--<span class="unidad">ppm</span></div>
        <div class="sub">Seguro &lt; 1000 ppm</div>
      </div>
      <div class="metrica">
        <div class="etiqueta">Saturacion Sensor</div>
        <div class="valor" id="val-sat">--<span class="unidad">%</span></div>
        <div class="sub">0% = limpio</div>
      </div>
      <div class="metrica">
        <div class="etiqueta">Valor ADC Crudo</div>
        <div class="valor" id="val-adc" style="font-size:1rem;">--<span class="unidad">/4095</span></div>
      </div>
      <div class="metrica">
        <div class="etiqueta">Voltaje Pin</div>
        <div class="valor" id="val-volt" style="font-size:1rem;">--<span class="unidad">V</span></div>
        <div class="sub">Max 3.3 V</div>
      </div>
    </div>
    <div class="fila">
      <div class="metrica">
        <div class="etiqueta">Condicion Gas</div>
        <div class="valor" id="val-gas" style="font-size:1rem;padding-top:4px;">--</div>
      </div>
      <div class="metrica">
        <div class="etiqueta">Nivel de Riesgo</div>
        <div class="valor" id="val-riesgo" style="font-size:1rem;padding-top:4px;">--</div>
        <div class="barra-riesgo">
          <div class="barra-riesgo-track">
            <div class="barra-riesgo-fill" id="barra-riesgo" style="width:0%;background:#238636;"></div>
          </div>
          <span id="txt-riesgo" style="font-size:0.68rem;color:var(--texto-sec);">1/5</span>
        </div>
      </div>
      <div class="metrica">
        <div class="etiqueta">Desviacion ADC</div>
        <div class="valor" id="val-desv" style="font-size:1rem;">--<span class="unidad">cuentas</span></div>
        <div class="sub">Estabilidad de lectura</div>
      </div>
      <div class="metrica">
        <div class="etiqueta">Alarma Hardware DO</div>
        <div class="valor" id="val-alarma" style="font-size:1rem;padding-top:4px;">--</div>
      </div>
    </div>

    <!-- Recomendacion de ventilacion -->
    <div class="recomendacion-box ok" id="caja-recomendacion">
      Ejecute un escaneo para ver la recomendacion de ventilacion.
    </div>

    <div style="margin-top:14px;">
      <div id="panel-escaneo-manual">
        <button class="btn btn-azul" onclick="ejecutarEscaneo()" id="btn-escaneo">Ejecutar Escaneo Ahora</button>
      </div>
      <div id="panel-escaneo-auto" style="display:none;font-size:0.78rem;color:var(--texto-sec);margin-top:8px;">
        Escaneo automatico cada 60 segundos. Proximo escaneo en: <span id="cuenta-regresiva">--</span> s
      </div>
    </div>
  </div>

  <!-- Control de actuadores (Modo Manual) -->
  <div class="tarjeta" id="panel-manual">
    <h2>Control de Actuadores</h2>
    <div class="fila">
      <div>
        <div style="margin-bottom:6px;font-size:0.78rem;color:var(--texto-sec);">
          <span class="indicador" id="ind-vent"></span>Ventilador 12V (Relay1 - P26)
          <span class="estado-chip" id="chip-vent">APAGADO</span>
        </div>
        <button class="btn btn-verde" onclick="toggleVentilador()" id="btn-vent">Encender Ventilador</button>
      </div>
      <div>
        <div style="margin-bottom:6px;font-size:0.78rem;color:var(--texto-sec);">
          <span class="indicador" id="ind-ven"></span>Ventanas Servo SG90 (P18)
          <span class="estado-chip" id="chip-ven">CERRADAS</span>
        </div>
        <button class="btn btn-azul" onclick="toggleVentanas()" id="btn-ven">Abrir Ventanas</button>
      </div>
    </div>
  </div>

  <!-- Panel modo automatico -->
  <div class="tarjeta" id="panel-auto" style="display:none;">
    <h2>Modo Automatico - Estado del Sistema</h2>
    <p style="font-size:0.82rem;color:var(--texto-sec);line-height:1.6;">
      El sistema gestiona los actuadores de forma autonoma:<br>
      &bull; Temperatura &gt; 28 C: ventilador activado via Relay1.<br>
      &bull; ADC gas &gt; 2500 o alarma DO activa: ventanas abiertas via servo.
    </p>
    <div class="separador"></div>
    <div class="fila">
      <div>
        <span class="indicador" id="ind-vent-a"></span>Ventilador:
        <span class="estado-chip" id="chip-vent-a">APAGADO</span>
      </div>
      <div>
        <span class="indicador" id="ind-ven-a"></span>Ventanas:
        <span class="estado-chip" id="chip-ven-a">CERRADAS</span>
      </div>
    </div>
  </div>

  <!-- Botones de emergencia -->
  <div class="tarjeta">
    <h2>Seguridad del Sistema</h2>
    <div class="fila">
      <button class="btn btn-rojo" onclick="paroEmergencia()" id="btn-paro">PARO DE EMERGENCIA</button>
      <button class="btn btn-gris" onclick="reiniciarCircuito()" id="btn-reinicio">Reiniciar Circuito</button>
    </div>
    <div style="font-size:0.72rem;color:var(--texto-sec);margin-top:8px;">
      El paro detiene todos los actuadores inmediatamente. El reinicio restaura el estado inicial seguro.
    </div>
  </div>

  <!-- Historial de escaneos FIFO -->
  <div class="tarjeta">
    <h2>Historial de Escaneos FIFO - Ultimos 10 reales</h2>
    <div class="overflow-x">
      <div id="contenedor-historial">
        <p style="font-size:0.78rem;color:var(--texto-sec);">Sin escaneos registrados aun. Ejecute un escaneo para comenzar.</p>
      </div>
    </div>
  </div>

</div>

<footer>
  <strong>Aula Inteligente - Control de Temperatura y Ventilacion</strong><br>
  CUCEI - Universidad de Guadalajara | Programacion Para Internet<br>
  <span id="footer-equipo">Cargando datos del equipo...</span><br>
  Fecha de entrega: <span id="footer-fecha">--</span>
</footer>

<script>
// =============================================================================
// JavaScript - Aula Inteligente (datos expandidos)
// =============================================================================

var estadoSistema = {
  modo:'manual', ventilador:false, ventanas:false, paro:false,
  temperatura:null, humedad:null, indice_calor:null, punto_rocio:null, confort:'--',
  gasAdc:null, gasVoltaje:null, gasDesviacion:null,
  gasPct:null, gasSaturacion:null, gasPpmCo2:null,
  gasCondicion:'--', gasRiesgo:0, gasRecomenda:'--', gasAlarma:false
};

var intervaloAutoEscaneo = null;
var cuentaRegresivaValor = 60;
var intervaloContador = null;

function peticion(ruta, datos) {
  var opciones = {method:'POST', headers:{'Content-Type':'application/json'}};
  if (datos) opciones.body = JSON.stringify(datos);
  return fetch('/'+ruta, opciones)
    .then(function(r){return r.json();})
    .catch(function(e){console.error('Error en peticion '+ruta+':', e); return null;});
}

function nd(v, suf) {
  if (v === null || v === undefined) return '--';
  return v + (suf ? suf : '');
}

function actualizarUI() {
  var s = estadoSistema;

  // DHT11
  document.getElementById('val-temp').innerHTML    = nd(s.temperatura) + '<span class="unidad">°C</span>';
  document.getElementById('val-hum').innerHTML     = nd(s.humedad)     + '<span class="unidad">%</span>';
  document.getElementById('val-ic').innerHTML      = nd(s.indice_calor)+ '<span class="unidad">°C</span>';
  document.getElementById('val-pr').innerHTML      = nd(s.punto_rocio) + '<span class="unidad">°C</span>';
  document.getElementById('val-confort').textContent = s.confort || '--';

  // MQ-135
  document.getElementById('val-aire').innerHTML    = nd(s.gasPct)        + '<span class="unidad">%</span>';
  document.getElementById('val-ppm').innerHTML     = nd(s.gasPpmCo2)     + '<span class="unidad">ppm</span>';
  document.getElementById('val-sat').innerHTML     = nd(s.gasSaturacion) + '<span class="unidad">%</span>';
  document.getElementById('val-adc').innerHTML     = nd(s.gasAdc)        + '<span class="unidad">/4095</span>';
  document.getElementById('val-volt').innerHTML    = nd(s.gasVoltaje)    + '<span class="unidad">V</span>';
  document.getElementById('val-gas').textContent   = s.gasCondicion || '--';
  document.getElementById('val-desv').innerHTML    = nd(s.gasDesviacion) + '<span class="unidad">cuentas</span>';

  // Barra de riesgo
  var riesgo = s.gasRiesgo || 0;
  var colores = ['','#238636','#3fb950','#e3b341','#f0883e','#da3633'];
  var barra = document.getElementById('barra-riesgo');
  barra.style.width = (riesgo * 20) + '%';
  barra.style.background = colores[riesgo] || '#238636';
  document.getElementById('val-riesgo').textContent = ['','1 - Optimo','2 - Aceptable','3 - Regular','4 - Deficiente','5 - Peligroso'][riesgo] || '--';
  document.getElementById('txt-riesgo').textContent = riesgo + '/5';

  // Alarma DO
  var alarmaEl = document.getElementById('val-alarma');
  alarmaEl.textContent = s.gasAlarma ? 'ALERTA ACTIVA' : 'Normal';
  alarmaEl.style.color = s.gasAlarma ? '#da3633' : '#3fb950';

  // Recomendacion
  var caja = document.getElementById('caja-recomendacion');
  caja.textContent = s.gasRecomenda || '--';
  caja.className = 'recomendacion-box';
  if (riesgo >= 4 || s.gasAlarma) caja.classList.add('peligro');
  else if (riesgo <= 2) caja.classList.add('ok');

  // Actuadores
  _indicador('vent',   s.ventilador, 'ENCENDIDO', 'APAGADO');
  _indicador('ven',    s.ventanas,   'ABIERTAS',  'CERRADAS');
  _chipAuto ('vent-a', s.ventilador, 'ENCENDIDO', 'APAGADO');
  _chipAuto ('ven-a',  s.ventanas,   'ABIERTAS',  'CERRADAS');

  var btnV = document.getElementById('btn-vent');
  if (s.ventilador) { btnV.textContent='Apagar Ventilador';  btnV.className='btn btn-rojo'; }
  else              { btnV.textContent='Encender Ventilador'; btnV.className='btn btn-verde'; }

  var btnVn = document.getElementById('btn-ven');
  if (s.ventanas) { btnVn.textContent='Cerrar Ventanas'; btnVn.className='btn btn-gris'; }
  else            { btnVn.textContent='Abrir Ventanas';  btnVn.className='btn btn-azul'; }

  // Paro de emergencia
  var alerta = document.getElementById('alerta-emergencia');
  var dot    = document.getElementById('estado-paro');
  if (s.paro) {
    alerta.style.display = 'block';
    dot.style.background = '#da3633';
    document.getElementById('btn-paro').disabled = true;
  } else {
    alerta.style.display = 'none';
    dot.style.background = '#238636';
    document.getElementById('btn-paro').disabled = false;
  }
}

function _indicador(id, on, txtOn, txtOff) {
  var ind  = document.getElementById('ind-'+id);
  var chip = document.getElementById('chip-'+id);
  if (!ind || !chip) return;
  ind.className    = on ? 'indicador on' : 'indicador';
  chip.textContent = on ? txtOn : txtOff;
  chip.className   = on ? 'estado-chip on' : 'estado-chip';
}

function _chipAuto(id, on, txtOn, txtOff) { _indicador(id, on, txtOn, txtOff); }

function _mapearRespuesta(r) {
  if (!r) return;
  estadoSistema.temperatura    = r.temperatura    !== undefined ? r.temperatura    : estadoSistema.temperatura;
  estadoSistema.humedad        = r.humedad        !== undefined ? r.humedad        : estadoSistema.humedad;
  estadoSistema.indice_calor   = r.indice_calor   !== undefined ? r.indice_calor   : estadoSistema.indice_calor;
  estadoSistema.punto_rocio    = r.punto_rocio    !== undefined ? r.punto_rocio    : estadoSistema.punto_rocio;
  estadoSistema.confort        = r.confort        || estadoSistema.confort;
  estadoSistema.gasAdc         = r.gas_adc        !== undefined ? r.gas_adc        : estadoSistema.gasAdc;
  estadoSistema.gasVoltaje     = r.gas_voltaje    !== undefined ? r.gas_voltaje    : estadoSistema.gasVoltaje;
  estadoSistema.gasDesviacion  = r.gas_desviacion !== undefined ? r.gas_desviacion : estadoSistema.gasDesviacion;
  estadoSistema.gasPct         = r.gas_pct        !== undefined ? r.gas_pct        : estadoSistema.gasPct;
  estadoSistema.gasSaturacion  = r.gas_saturacion !== undefined ? r.gas_saturacion : estadoSistema.gasSaturacion;
  estadoSistema.gasPpmCo2      = r.gas_ppm_co2    !== undefined ? r.gas_ppm_co2    : estadoSistema.gasPpmCo2;
  estadoSistema.gasCondicion   = r.gas_condicion  || estadoSistema.gasCondicion;
  estadoSistema.gasRiesgo      = r.gas_riesgo     !== undefined ? r.gas_riesgo     : estadoSistema.gasRiesgo;
  estadoSistema.gasRecomenda   = r.gas_recomenda  || estadoSistema.gasRecomenda;
  estadoSistema.gasAlarma      = r.gas_alarma     !== undefined ? r.gas_alarma     : estadoSistema.gasAlarma;
  if (r.ventilador !== undefined) estadoSistema.ventilador = r.ventilador;
  if (r.ventanas   !== undefined) estadoSistema.ventanas   = r.ventanas;
  if (r.paro       !== undefined) estadoSistema.paro       = r.paro;
}

// --- Controles ---
function toggleVentilador() {
  if (estadoSistema.paro) return;
  peticion('ventilador', {accion: estadoSistema.ventilador ? 'apagar' : 'encender'}).then(function(r) {
    if (r) { estadoSistema.ventilador = r.ventilador; actualizarUI(); }
  });
}

function toggleVentanas() {
  if (estadoSistema.paro) return;
  peticion('ventanas', {accion: estadoSistema.ventanas ? 'cerrar' : 'abrir'}).then(function(r) {
    if (r) { estadoSistema.ventanas = r.ventanas; actualizarUI(); }
  });
}

function ejecutarEscaneo() {
  var btn = document.getElementById('btn-escaneo');
  btn.disabled = true;
  btn.textContent = 'Escaneando...';
  peticion('escanear', {}).then(function(r) {
    if (r) { _mapearRespuesta(r); actualizarUI(); if (r.historial) actualizarTablaHistorial(r.historial); }
    btn.disabled = false;
    btn.textContent = 'Ejecutar Escaneo Ahora';
  });
}

function ejecutarEscaneoAuto() {
  peticion('escanear_auto', {}).then(function(r) {
    if (r) { _mapearRespuesta(r); actualizarUI(); if (r.historial) actualizarTablaHistorial(r.historial); }
  });
}

function paroEmergencia() {
  peticion('paro', {}).then(function(r) {
    if (r) {
      estadoSistema.paro = true;
      estadoSistema.ventilador = false;
      estadoSistema.ventanas   = false;
      actualizarUI();
      if (intervaloAutoEscaneo) { clearInterval(intervaloAutoEscaneo); clearInterval(intervaloContador); }
    }
  });
}

function reiniciarCircuito() {
  peticion('reiniciar', {}).then(function(r) {
    if (r) {
      estadoSistema.paro = false;
      estadoSistema.ventilador = false;
      estadoSistema.ventanas   = false;
      actualizarUI();
      if (estadoSistema.modo === 'automatico') iniciarAutoEscaneo();
    }
  });
}

function cambiarModo(modo) {
  estadoSistema.modo = modo;
  document.getElementById('chip-modo').textContent = modo === 'manual' ? 'MANUAL' : 'AUTOMATICO';
  document.getElementById('tab-manual').className  = 'modo-tab' + (modo === 'manual'     ? ' activo' : '');
  document.getElementById('tab-auto').className    = 'modo-tab' + (modo === 'automatico' ? ' activo' : '');
  document.getElementById('panel-manual').style.display         = modo === 'manual'     ? 'block' : 'none';
  document.getElementById('panel-auto').style.display           = modo === 'automatico' ? 'block' : 'none';
  document.getElementById('panel-escaneo-manual').style.display = modo === 'manual'     ? 'block' : 'none';
  document.getElementById('panel-escaneo-auto').style.display   = modo === 'automatico' ? 'block' : 'none';
  peticion('modo', {modo: modo});
  if (modo === 'automatico') { if (!estadoSistema.paro) iniciarAutoEscaneo(); }
  else { if (intervaloAutoEscaneo) { clearInterval(intervaloAutoEscaneo); clearInterval(intervaloContador); } }
}

function iniciarAutoEscaneo() {
  cuentaRegresivaValor = 60;
  ejecutarEscaneoAuto();
  if (intervaloContador)    clearInterval(intervaloContador);
  if (intervaloAutoEscaneo) clearInterval(intervaloAutoEscaneo);
  intervaloContador = setInterval(function() {
    cuentaRegresivaValor--;
    document.getElementById('cuenta-regresiva').textContent = cuentaRegresivaValor;
    if (cuentaRegresivaValor <= 0) cuentaRegresivaValor = 60;
  }, 1000);
  intervaloAutoEscaneo = setInterval(function() {
    cuentaRegresivaValor = 60;
    ejecutarEscaneoAuto();
  }, 60000);
}

// --- Tabla de historial FIFO con todos los campos ---
function actualizarTablaHistorial(historial) {
  var cont = document.getElementById('contenedor-historial');
  if (!historial || historial.length === 0) {
    cont.innerHTML = '<p style="font-size:0.78rem;color:var(--texto-sec);">Sin escaneos registrados aun.</p>';
    return;
  }
  var t = '<table class="tabla-historial"><thead><tr>';
  t += '<th>#</th><th>Seg</th>';
  // DHT11
  t += '<th>Temp(°C)</th><th>Hum(%)</th><th>I.Calor(°C)</th><th>P.Rocio(°C)</th><th>Confort</th>';
  // MQ-135
  t += '<th>ADC</th><th>Volt(V)</th><th>Desv</th><th>Calidad(%)</th><th>Sat(%)</th><th>CO2(ppm)</th><th>Condicion</th><th>Riesgo</th><th>Alarma DO</th>';
  t += '</tr></thead><tbody>';
  var colores = ['','#3fb950','#3fb950','#e3b341','#f0883e','#da3633'];
  for (var i = historial.length - 1; i >= 0; i--) {
    var r = historial[i];
    var ar = r.gas_alarma ? '<span style="color:#da3633;">SI</span>' : 'No';
    var rc = colores[r.gas_riesgo] || '';
    t += '<tr>';
    t += '<td>' + (historial.length - i) + '</td>';
    t += '<td>' + (r.seg_boot !== undefined ? r.seg_boot : '--') + '</td>';
    // DHT11
    t += '<td>' + (r.temperatura  !== null && r.temperatura  !== undefined ? r.temperatura  : '--') + '</td>';
    t += '<td>' + (r.humedad      !== null && r.humedad      !== undefined ? r.humedad      : '--') + '</td>';
    t += '<td>' + (r.indice_calor !== null && r.indice_calor !== undefined ? r.indice_calor : '--') + '</td>';
    t += '<td>' + (r.punto_rocio  !== null && r.punto_rocio  !== undefined ? r.punto_rocio  : '--') + '</td>';
    t += '<td>' + (r.confort || '--') + '</td>';
    // MQ-135
    t += '<td>' + (r.gas_adc        !== null && r.gas_adc        !== undefined ? r.gas_adc        : '--') + '</td>';
    t += '<td>' + (r.gas_voltaje    !== null && r.gas_voltaje    !== undefined ? r.gas_voltaje    : '--') + '</td>';
    t += '<td>' + (r.gas_desviacion !== null && r.gas_desviacion !== undefined ? r.gas_desviacion : '--') + '</td>';
    t += '<td>' + (r.gas_pct        !== null && r.gas_pct        !== undefined ? r.gas_pct        : '--') + '</td>';
    t += '<td>' + (r.gas_saturacion !== null && r.gas_saturacion !== undefined ? r.gas_saturacion : '--') + '</td>';
    t += '<td>' + (r.gas_ppm_co2   !== null && r.gas_ppm_co2   !== undefined ? r.gas_ppm_co2   : '--') + '</td>';
    t += '<td>' + (r.gas_condicion || '--') + '</td>';
    t += '<td style="color:' + rc + ';">' + (r.gas_riesgo !== undefined ? r.gas_riesgo+'/5' : '--') + '</td>';
    t += '<td>' + ar + '</td>';
    t += '</tr>';
  }
  t += '</tbody></table>';
  cont.innerHTML = t;
}

function cargarEstadoInicial() {
  fetch('/estado').then(function(r){return r.json();}).then(function(r) {
    if (!r) return;
    _mapearRespuesta(r);
    estadoSistema.modo = r.modo || 'manual';
    if (r.equipo) {
      var txt = r.equipo.map(function(m){ return m.nombre + ' (' + m.registro + ')'; }).join(' | ');
      if (r.asignatura) txt += ' | ' + r.asignatura;
      document.getElementById('footer-equipo').textContent = txt;
    }
    if (r.fecha) document.getElementById('footer-fecha').textContent = r.fecha;
    cambiarModo(estadoSistema.modo);
    actualizarUI();
    if (r.historial) actualizarTablaHistorial(r.historial);
  }).catch(function(e){ console.error('Error carga inicial:', e); });
}

window.onload = cargarEstadoInicial;
</script>
</body>
</html>"""

# El servidor accede a CABECERA_HTML y CUERPO_HTML por separado
# y los envia en fragmentos para no saturar la RAM de la ESP32.