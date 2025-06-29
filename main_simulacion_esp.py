import network
import time
import ujson
from machine import Pin
from umqtt import MQTTClient
import urandom
import uhashlib
import ubinascii
import ucryptolib

# --- Configuración protegida ---
SECRET_KEY = b"claveAES128bits!"  # exactamente 16 bytes
PIN_AUTENTICACION = "1234"
UMBRAL_TEMP = 30
UMBRAL_HUM = 30

# --- Variables protegidas ---
bomba_pin = Pin(4, Pin.OUT)

# --- AES ECB Encryption ---
def cifrar_valor(valor):
    aes = ucryptolib.aes(SECRET_KEY, 1)  # AES.MODE_ECB
    valor_str = str(valor)
    # Relleno manual con espacios si es más corto que 16
    while len(valor_str) < 16:
        valor_str += ' '
    valor_str = valor_str[:16]  # Cortar si se pasa
    encrypted = aes.encrypt(valor_str.encode())
    return ubinascii.b2a_base64(encrypted).decode().strip()

# --- Simulación de sensor ---
def leer_sensor():
    temp = urandom.getrandbits(4) + 25
    hum = urandom.getrandbits(4) + 20
    return str(temp), str(hum)

# --- Cifrado de datos (hash para integridad) ---
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
    bomba_estado = int(temp) > UMBRAL_TEMP and int(hum) < UMBRAL_HUM
    bomba_pin.value(1 if bomba_estado else 0)

    payload = {
        "temp": cifrar_valor(temp),
        "hum": cifrar_valor(hum),
        "bomba_riego": bomba_estado,
        "pin": cifrar_valor(PIN_AUTENTICACION)
    }
    json_data = ujson.dumps(payload)
    firma = firmar_datos(json_data.encode())
    mensaje_final = ujson.dumps({"data": payload, "firma": firma})
    mqtt.publish("sensor/dht11", mensaje_final)
    print("Publicado:", mensaje_final)
    time.sleep(3)
