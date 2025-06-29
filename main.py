import flet as ft
import paho.mqtt.client as mqtt
import json
import threading
import time
import hashlib

# Configuración protegida
SECRET_KEY = b"miclave1234567890"
PIN_AUTORIZADO = "1234"

# Variables globales
temperatura = "---"
humedad = "---"
bomba_riego = False
page = None

# Validar firma de datos
def validar_datos(data, firma):
    json_bytes = json.dumps(data).encode()
    h = hashlib.sha256()
    h.update(json_bytes + SECRET_KEY)
    return h.hexdigest() == firma

# Conexión MQTT
def on_connect(client, userdata, flags, rc):
    print("Conectado al broker MQTT")
    client.subscribe("sensor/dht11")

def on_message(client, userdata, msg):
    global temperatura, humedad, bomba_riego
    try:
        payload = json.loads(msg.payload)
        data = payload.get("data")
        firma = payload.get("firma")
        if not validar_datos(data, firma):
            print("⚠️ Firma inválida. Ignorando mensaje.")
            return

        if data.get("pin") != PIN_AUTORIZADO:
            print("⚠️ PIN no autorizado")
            return

        temperatura = data["temp"]
        humedad = data["hum"]
        bomba_riego = data["bomba_riego"]

        print(f"Datos recibidos: Temp={temperatura}°C, Hum={humedad}%, Riego={bomba_riego}")
        update_ui()
    except Exception as e:
        print("Error al procesar mensaje:", e)


def update_ui():
    page.update()

# Configura cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    mqtt_client.connect("mqtt.eclipseprojects.io", 1883, 60)
    mqtt_client.loop_forever()

# Interfaz Flet
def main(p):
    global page
    page = p
    page.title = "Panel de Cultivo Seguro"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT

    txt_temp = ft.Text(f"Temperatura: {temperatura}°C", size=24)
    txt_hum = ft.Text(f"Humedad: {humedad}%", size=24)
    txt_riego = ft.Text(f"RIEGO DESACTIVADO", size=28, weight=ft.FontWeight.BOLD, color="blue")

    page.add(
        ft.Column([
            ft.Text("Estado del Sensor", size=40, weight=ft.FontWeight.BOLD),
            txt_temp,
            txt_hum,
            txt_riego
        ], alignment=ft.MainAxisAlignment.CENTER)
    )

    def update_task():
        while True:
            txt_temp.value = f"Temperatura: {temperatura}°C"
            txt_hum.value = f"Humedad: {humedad}%"
            txt_riego.value = "RIEGO ACTIVADO" if bomba_riego else "RIEGO DESACTIVADO"
            txt_riego.color = "green" if bomba_riego else "red"
            page.update()
            time.sleep(2)

    threading.Thread(target=update_task, daemon=True).start()

# Iniciar MQTT en segundo plano
threading.Thread(target=start_mqtt, daemon=True).start()

ft.app(target=main, view=ft.WEB_BROWSER)

