import network
import time
import ujson
from machine import Pin
from umqtt import MQTTClient
import urandom
import uhashlib

# --- Configuración protegida ---
SECRET_KEY = b"miclave1234567890"
PIN_AUTENTICACION = "1234"
UMBRAL_TEMP = 30
UMBRAL_HUM = 30

# --- Variables protegidas ---
bomba_pin = Pin(4, Pin.OUT)

# --- Función de autenticación simple por PIN ---
def validar_pin(pin):
    return pin == PIN_AUTENTICACION

# --- Simulación de sensor ---
def leer_sensor():
    temp = urandom.getrandbits(4) + 25
    hum = urandom.getrandbits(4) + 20
    return temp, hum

# --- Cifrado de datos (simulado con hash para integridad) ---
def firmar_datos(data_json):
    h = uhashlib.sha256()
    h.update(data_json + SECRET_KEY)
    return h.digest().hex()

# --- Conexión WiFi ---
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect("R13Pro+5G", "12345678j")
while not sta.isconnected():
    time.sleep(1)
print("Conectado a WiFi")

# --- Conexión MQTT ---
mqtt = MQTTClient("esp_sim", "mqtt.eclipseprojects.io")
mqtt.connect()

while True:
    temp, hum = leer_sensor()
    bomba_estado = temp > UMBRAL_TEMP and hum < UMBRAL_HUM
    bomba_pin.value(1 if bomba_estado else 0)

    payload = {
        "temp": temp,
        "hum": hum,
        "bomba_riego": bomba_estado,
        "pin": PIN_AUTENTICACION
    }
    json_data = ujson.dumps(payload)
    firma = firmar_datos(json_data.encode())
    mensaje_final = ujson.dumps({"data": payload, "firma": firma})
    mqtt.publish("sensor/dht11", mensaje_final)
    print("Publicado:", mensaje_final)
    time.sleep(3)